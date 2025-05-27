import os
import argparse
import logging
import pandas as pd
from pandasql import sqldf
import json
from vladiate import Vlad, logs
from vladiate.validators import UniqueValidator, SetValidator, IntValidator, Validator, ValidationException, RegexValidator
from vladiate.inputs import LocalFile
from io import StringIO
import tempfile
import traceback
import re
# Set up argparse
from .utils import is_overlapping,update_row,textset
def eval_quantity(docId,input,answer):
   '''
        F1的分数乘10 减去 （1-准确率） * 100，希望能减少不必要幻觉
   '''
   
   try:
        goldfs = []
        subdfs = []
        subnames = []
        sub = pd.read_csv(StringIO(input),sep = '\t')
        annot_df = sub.copy()
        text = textset[docId]
        used_ranges = []  # 保存所有已标记的区间
        quantity_counter = 1
        updated_rows = []
        found=False
        quantity_text = ""
        penal = 0
        if answer == "" and not sub.empty:
            print("not null penalty")
            for index,row in sub.iterrows():
                penal -= 1000
            return penal
        if answer == "" and sub.empty:
            return 10
        for index, row in annot_df.iterrows():
            quantity_text = str(row.get('text', ''))
            found=False

            if row['annotType'] != 'Quantity':
                raise ValueError(f"Invalid annotType: {row['annotType']} (Only 'Quantity' allowed)")

            if re.fullmatch(r'T\d+', str(row.get('text', ''))):
                raise ValueError(f"Invalid text label: {row['text']} (T-labels like T1, T2 not allowed)")

            for match in re.finditer(re.escape(quantity_text), text):
                start = match.start()
                end = match.end()
                if not is_overlapping(start, end, used_ranges):
                    used_ranges.append((start, end))
                    updated_row = update_row(row, start, end, quantity_counter, docId)
                    updated_rows.append(updated_row)
                    quantity_counter += 1
                    found = True
                    break
            if not found:
                print(f"Quantity '{quantity_text}' not found without overlap in the text.")
        # 将更新后的数据写入新的 TSV 文件
        updated_df = pd.DataFrame(updated_rows)
        # print(updated_df)
        sub = updated_df
        # pandasql library to handle all our joins and checks.
        gold = pd.read_csv(StringIO(answer),sep = '\t')

        # Forcing some types, and also setting empty fields for later lambdas
        gold['annotSet'].astype('int')
        gold['startOffset'].astype('int')
        gold['endOffset'].astype('int')
        sub['annotSet'].astype('int')
        sub['startOffset'].astype('int')
        sub['endOffset'].astype('int')
        gold['EM'] = None
        gold['F1'] = None
        gold['maxF1'] = None
        sub['EM'] = None
        sub['F1'] = None
        sub['maxF1'] = None


      #print(gold.shape)
      #print(sub.shape)

      # Report annotation type counts for both Gold and Submission
        # for annotType in ["Quantity", "MeasuredProperty", "MeasuredEntity", "Qualifier"]:
            # print("Gold count of " + annotType + ": " + str(len(gold.loc[gold["annotType"] == annotType].index)))
        # print("")
        # for annotType in ["Quantity", "MeasuredProperty", "MeasuredEntity", "Qualifier"]:
            # print("Submission count of " + annotType + ": " + str(len(sub.loc[sub["annotType"] == annotType].index)))
        # print("")

      # Start processing quantities

        goldQuants = gold.loc[gold["annotType"] == "Quantity"]
        subQuants = sub.loc[sub["annotType"] == "Quantity"]
      # pandasql to get our matches for Quantity

      # Note that we are processing everything keyed on Quantities.
      # Any even partially matched quantity will be marked as a match
      # All other components will only be credited if associated with a matching quantity
      # So if a submission has identified the MeasuredEntity spans correctly
      # but has them assocaited with incorrectly matched quantities
      # credit will not be given for those matches.

      # Matching here is done in two steps.
      # matching quantities in the submission file are given appropriate
      # annotSet and annotId values drawn from teh matching gold data

        q = """SELECT
            s.annotSet, g.annotSet as gAnnotSet, s.docId, s.annotType, s.annotId,
            g.annotId as gAnnotId, s.startOffset, s.endOffset, s.text, s.EM, s.F1, s.maxF1
            FROM
            subQuants s
            JOIN
            goldQuants g
                ON (s.docId = g.docId
                AND ((s.startOffset >= g.startOffset AND s.startOffset <= g.endOffset)
                OR (s.endOffset >= g.startOffset AND s.endOffset <= g.endOffset)
                OR (g.startOffset >= s.startOffset AND g.startOffset <= s.endOffset)
                OR (g.endOffset >= s.startOffset AND g.endOffset <= s.endOffset)))"""
        env = {
            'subQuants' : subQuants,
            'goldQuants':goldQuants
        }
        subMatches = sqldf(q, env)

      # Those matching annotSet and annotId values are then used to build a joined dataset

        q = """SELECT
            l.annotSet, l.gAnnotSet, l.docId, l.annotId, l.gAnnotId,
            l.startOffset as aStart, l.endOffset as aEnd, l.text as aText,
            r.startOffset as gStart, r.endOffset as gEnd, r.text as gText,
            l.EM, l.F1, l.maxF1
            FROM
            subMatches l
            JOIN
            goldQuants r
                ON (l.docId = r.docId
                AND l.gAnnotSet = r.annotSet
                AND l.gAnnotId = r.annotId)"""

        env = {
            'subMatches':subMatches,
            'goldQuants':goldQuants
        }
        quantityMatches = sqldf(q, env)

        # within the joined dataset, exact match (EM) scores are assigned if the
        # submission and gold start and end offsets align exactly.

        quantityMatches['EM'] = quantityMatches.apply (lambda x: 1.0 if (x.aStart == x.gStart and x.aEnd == x.gEnd) else 0, axis = 1 )

      # For a SQuAD-style "F1" overlap score
      # we calculate token level overlap between the submission and gold endpoints
      # Tokenization is done using a simple space delimited method
        def calcF1 (row):
            penalty = 0
            aTokensSize = len(row.aText.split(" "))
            gTokensSize = len(row.gText.split(" "))
            overlapStart = max(row.aStart, row.gStart)
            overlapEnd = min(row.aEnd, row.gEnd)
            overlapSubStrStart = 0
            overlapSubStrLen = int(overlapEnd - overlapStart)
            if (overlapStart > row.aStart):
                overlapSubStrStart = int(overlapStart - row.aStart)
            overlapText = row.aText[overlapSubStrStart:overlapSubStrStart+overlapSubStrLen]
            overlapTokenCnt = len(overlapText.split(" "))

            precision = 1.0 * overlapTokenCnt / aTokensSize
            recall = 1.0 * overlapTokenCnt / gTokensSize
            penalty = 1-precision
            penalty2 = 1-recall
            F1 = (2 * precision * recall) / (precision + recall)
            return F1 - penalty * 100

        quantityMatches['F1'] = quantityMatches.apply (lambda x: calcF1(x), axis = 1 )

        # If there are multiple matches, we will give the highest F1 score.
        quantityMatches['maxF1'] = quantityMatches.groupby(['docId', 'annotId'])['F1'].transform('max')

      # We also create sets of submission only Quantities and Gold Only Quantiites
      # These will be scored as both EM and F1 = 0 in the final evaluation,
      # so that precision and recall impact the overall score.

        q = """SELECT
            l.*
            FROM
            subQuants l
            LEFT JOIN
            quantityMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.annotId = r.annotId)
                WHERE r.docId is NULL"""
        env = {
            "subQuants":subQuants,
            "quantityMatches":quantityMatches
        }
        subOnlyQuants = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldQuants l
            LEFT JOIN
            quantityMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.annotId = r.gAnnotId)
                WHERE r.docId is NULL"""

        env = {
            "goldQuants":goldQuants,
            "quantityMatches":quantityMatches
        }
        goldOnlyQuants = sqldf(q, env)

        # Next, we collect those alignments from the quantity matches
        # And propagate them through the rest of the submission.

        # Note that (TODO) more than 1 submission value can match the same gold data
        # and those scores will be duplicated. However, beyond the Quantity scores, only 1 gold datapoint
        # can match a given submission annotSet. (TODO: Confirm that I'm not describing this backward.)

        annotSetAlignments = quantityMatches[["docId", "annotSet", "gAnnotSet"]].rename(columns={"gAnnotSet":"matchAnnotSet"})
        annotSetAlignmentsDict = annotSetAlignments.groupby('docId').apply(lambda x: dict(zip(x.annotSet, x.matchAnnotSet))).to_dict()

        # Update submission data with corresponding gold annotSet if applicable.
        sub["gAnnotSet"] = None
        sub["gAnnotSet"] = sub.apply(lambda x: annotSetAlignmentsDict[x.docId][x.annotSet] if x.docId in annotSetAlignmentsDict and x.annotSet in annotSetAlignmentsDict[x.docId] else None , axis = 1)

        # Now we'll process our units
        # This requires unpacking that data from the json in the other column

        goldUnits = goldQuants[goldQuants.other.notnull()].copy()
        goldUnits['json'] = goldUnits.apply (lambda x: json.loads(str(x.other)) if str(x.other) != "nan" else "", axis = 1 )
        goldUnits['unit'] = goldUnits.apply (lambda x: x.json["unit"] if "unit" in x.json.keys() else "", axis = 1)
        goldUnits = goldUnits[goldUnits.unit != ""][["docId", "annotSet", "annotType", "startOffset", "endOffset", "annotId", "text", "unit"]]

        #print(sub[sub["annotType"] == "Quantity"].head())

        subUnits = sub[sub["annotType"] == "Quantity"].copy() #and sub.other.notnull()]
        subUnits = subUnits[subUnits.other.notnull()]
        subUnits['json'] = None
        subUnits['unit'] = None
        if not subUnits.empty:
            subUnits['json'] = subUnits.apply (lambda x: json.loads(str(x.other)) if str(x.other) != "nan" else "", axis = 1 )
            subUnits['unit'] = subUnits.apply (lambda x: x.json["unit"] if "unit" in x.json.keys() else "", axis = 1)
        #print(subUnits.head())
        subUnits = subUnits[subUnits.unit != ""][["docId", "annotSet", "gAnnotSet", "annotType", "startOffset", "endOffset", "annotId", "text", "unit", "EM", "F1", "maxF1"]]

        # We'll now use our same matching strategy to score units,
        # ensuring that the text of the unit matches.
        q = """SELECT
            s.gAnnotSet as matchAnnotSet, g.annotSet as gAnnotSet, s.docId, s.annotType, s.annotId,
            g.annotId as gAnnotId, s.startOffset, s.endOffset, s.text as sText, g.text as gText,
            s.unit as sUnit, g.unit as gUnit, s.EM, s.F1, s.maxF1
            FROM
            subUnits s
            JOIN
            goldUnits g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND s.unit = g.unit)"""
        env = {
            "subUnits":subUnits,
            "goldUnits":goldUnits
        }
        unitMatches = sqldf(q, env)

        # EM and F1 here are both binary (no partial overlap matches)
        unitMatches['EM'] = unitMatches.apply (lambda x: 1.0 if (x.sUnit == x.gUnit) else 0, axis = 1 )
        unitMatches['F1'] = unitMatches.apply (lambda x: 1.0 if (x.sUnit == x.gUnit) else 0, axis = 1 )

        # And again, submission only and gold set only units
        q = """SELECT
            l.*
            FROM
            subUnits l
            LEFT JOIN
            unitMatches r
                ON (l.docId = r.docId
                AND l.gAnnotSet = r.gAnnotSet)
                WHERE r.docId is NULL"""
        env = {
            "subUnits":subUnits,
            "unitMatches":unitMatches
        }
        subOnlyUnits = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldUnits l
            LEFT JOIN
            unitMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet)
                WHERE r.docId is NULL"""
        env = {
            "goldUnits":goldUnits,
            "unitMatches":unitMatches
        }
        goldOnlyUnits = sqldf(q, env)

        # We do the same routine for MeasuredEntities
        goldEntities = gold.loc[gold["annotType"] == "MeasuredEntity"]
        subEntities = sub.loc[sub["annotType"] == "MeasuredEntity"]

        q = """SELECT
            s.annotSet, s.gAnnotSet, s.docId, s.annotType, s.annotId,
            g.annotId as gAnnotId, s.startOffset as aStart, g.startOffset as gStart,
            s.endOffset as aEnd, g.endOffset as gEnd, s.text as aText, g.text as gText, s.other,
            s.EM, s.F1, s.maxF1
            FROM
            subEntities s
            JOIN
            goldEntities g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND ((s.startOffset >= g.startOffset AND s.startOffset <= g.endOffset)
                OR (s.endOffset >= g.startOffset AND s.endOffset <= g.endOffset)
                OR (g.startOffset >= s.startOffset AND g.startOffset <= s.endOffset)
                OR (g.endOffset >= s.startOffset AND g.endOffset <= s.endOffset)))"""

        env = {
            "subEntities":subEntities,
            "goldEntities":goldEntities
        }
        entityMatches = sqldf(q, env)
        # print(entityMatches)
        entityMatches['EM'] = entityMatches.apply (lambda x: 1.0 if (x.aStart == x.gStart and x.aEnd == x.gEnd) else 0, axis = 1 )
        if not entityMatches.empty:
            entityMatches['F1'] = entityMatches.apply (lambda x: calcF1(x), axis = 1 )
        else:
            entityMatches['F1'] = 0
        entityMatches['maxF1'] = entityMatches.groupby(['docId', 'annotId'])['F1'].transform('max')

        q = """SELECT
            l.*
            FROM
            subEntities l
            LEFT JOIN
            entityMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.annotId = r.annotId)
                WHERE r.docId is NULL"""
        env = {
            "subEntities":subEntities,
            "entityMatches":entityMatches
        }
        subOnlyEntities = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldEntities l
            LEFT JOIN
            entityMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.annotId = r.gAnnotId)
                WHERE r.docId is NULL"""
        env = {
            "goldEntities":goldEntities,
            "entityMatches":entityMatches
        }
        goldOnlyEntities = sqldf(q, env)

        # We do the same routine for MeasuredProperties
        goldProperties = gold.loc[gold["annotType"] == "MeasuredProperty"]
        subProperties = sub.loc[sub["annotType"] == "MeasuredProperty"]

        q = """SELECT
            s.annotSet, s.gAnnotSet, s.docId, s.annotType, s.annotId,
            g.annotId as gAnnotId, s.startOffset as aStart, g.startOffset as gStart,
            s.endOffset as aEnd, g.endOffset as gEnd, s.text as aText, g.text as gText, s.other,
            s.EM, s.F1, s.maxF1
            FROM
            subProperties s
            JOIN
            goldProperties g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND ((s.startOffset >= g.startOffset AND s.startOffset <= g.endOffset)
                OR (s.endOffset >= g.startOffset AND s.endOffset <= g.endOffset)
                OR (g.startOffset >= s.startOffset AND g.startOffset <= s.endOffset)
                OR (g.endOffset >= s.startOffset AND g.endOffset <= s.endOffset)))"""
        env = {
            "subProperties":subProperties,
            "goldProperties":goldProperties
        }
        propertyMatches = sqldf(q, env)
        propertyMatches['EM'] = propertyMatches.apply (lambda x: 1.0 if (x.aStart == x.gStart and x.aEnd == x.gEnd) else 0, axis = 1 )
        if not propertyMatches.empty:
            propertyMatches['F1'] = propertyMatches.apply (lambda x: calcF1(x), axis = 1 )
        else:
            propertyMatches['F1'] = 0
        propertyMatches['maxF1'] = propertyMatches.groupby(['docId', 'annotId'])['F1'].transform('max')

        q = """SELECT
            l.*
            FROM
            subProperties l
            LEFT JOIN
            propertyMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.annotId = r.annotId)
                WHERE r.docId is NULL"""
        env = {
            "subProperties":subProperties,
            "propertyMatches":propertyMatches
        }
        subOnlyProperties = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldProperties l
            LEFT JOIN
            propertyMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.annotId = r.gAnnotId)
                WHERE r.docId is NULL"""
        env = {
            "goldProperties":goldProperties,
            "propertyMatches":propertyMatches
        }
        goldOnlyProperties = sqldf(q, env)

        # We do the same routine for Qualifiers:
        goldQualifiers = gold.loc[gold["annotType"] == "Qualifier"]
        subQualifiers = sub.loc[sub["annotType"] == "Qualifier"]

        q = """SELECT
            s.annotSet, s.gAnnotSet, s.docId, s.annotType, s.annotId,
            g.annotId as gAnnotId, s.startOffset as aStart, g.startOffset as gStart,
            s.endOffset as aEnd, g.endOffset as gEnd, s.text as aText, g.text as gText, s.other,
            s.EM, s.F1, s.maxF1
            FROM
            subQualifiers s
            JOIN
            goldQualifiers g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND ((s.startOffset >= g.startOffset AND s.startOffset <= g.endOffset)
                OR (s.endOffset >= g.startOffset AND s.endOffset <= g.endOffset)
                OR (g.startOffset >= s.startOffset AND g.startOffset <= s.endOffset)
                OR (g.endOffset >= s.startOffset AND g.endOffset <= s.endOffset)))"""
        env = {
            "subQualifiers":subQualifiers,
            "goldQualifiers":goldQualifiers
        }
        qualifierMatches = sqldf(q, env)
        # qualifierMatches['EM'] = None
        # qualifierMatches['F1'] = None
        # qualifierMatches['maxF1'] = None

        qualifierMatches['EM'] = qualifierMatches.apply (lambda x: 1.0 if (x.aStart == x.gStart and x.aEnd == x.gEnd) else 0, axis = 1 )
        if not qualifierMatches.empty:
            qualifierMatches['F1'] = qualifierMatches.apply (lambda x: calcF1(x), axis = 1 )
        else:
            qualifierMatches['F1'] = 0
        qualifierMatches['maxF1'] = qualifierMatches.groupby(['docId', 'annotId'])['F1'].transform('max')


        q = """SELECT
            l.*
            FROM
            subQualifiers l
            LEFT JOIN
            qualifierMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.annotId = r.annotId)
                WHERE r.docId is NULL"""
        env = {
            "subQualifiers":subQualifiers,
            "qualifierMatches":qualifierMatches
        }
        subOnlyQualifiers = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldQualifiers l
            LEFT JOIN
            qualifierMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.annotId = r.gAnnotId)
                WHERE r.docId is NULL"""
        env = {
            "goldQualifiers":goldQualifiers,
            "qualifierMatches":qualifierMatches
        }
        goldOnlyQualifiers = sqldf(q, env)

        # Now we will process and score all relationships.
        # Relations are drawn from the "Other" column of the TSV data
        # The "source" of a relationship is the annotation associated with a given row.
        # It's relation type and "target" are established in the "other" field
        # Our validation ensures that any annotation of type MeasuredEntity, MeasuredProperty, or Qualifier
        # Includes the appropriate relationship.

        # We pull the relationships out of the json data:
        tmpgRels = gold.loc[gold["annotType"].isin(["MeasuredEntity", "MeasuredProperty", "Qualifier"])].copy()
        tmpgRels['json'] = tmpgRels.apply (lambda x: json.loads(str(x.other)) if str(x.other) != "nan" else "", axis = 1 )
        tmpgRels['relType'] = tmpgRels.apply (lambda x: list(x.json.keys())[0], axis = 1 )
        tmpgRels['target'] = tmpgRels.apply (lambda x: list(x.json.values())[0], axis = 1 )
        tmpgRels['src'] = tmpgRels.apply (lambda x: x.annotId, axis=1)
        # print(tmpgRels)
        goldRels = tmpgRels[["docId", "annotSet", "annotType", "relType", "src", "target"]]

        tmpsRels = sub.loc[sub["annotType"].isin(["MeasuredEntity", "MeasuredProperty", "Qualifier"])].copy()
        # print(tmpsRels)
        tmpsRels['json'] = None
        tmpsRels['relType'] = None
        tmpsRels['target'] = None
        tmpsRels['src'] = None
        if not tmpsRels.empty:
            tmpsRels['json'] = tmpsRels.apply (lambda x: json.loads(str(x.other)) if str(x.other) != "nan" else "", axis = 1 )
            tmpsRels['relType'] = tmpsRels.apply (lambda x: list(x.json.keys())[0], axis = 1 )
            tmpsRels['target'] = tmpsRels.apply (lambda x: list(x.json.values())[0], axis = 1 )
            tmpsRels['src'] = tmpsRels.apply (lambda x: x.annotId, axis=1)
        # print(tmpsRels)
        subRels = tmpsRels[["docId", "annotSet", "gAnnotSet", "annotType", "relType", "src", "target"]]

        # We process "HasQuantity"
        # Source should be either a MeasuredEntity or a MeasuredProperty
        # Target should be a Quantity
        # We will build out the submission relationships
        # Grab the corresponding gold set ids for any matching source and target endpoint
        # And score accordingly.

        goldHasQuant = goldRels.loc[goldRels["relType"] == "HasQuantity"]
        subHasQuant = subRels.loc[subRels["relType"] == "HasQuantity"]
        # print(goldHasQuant)
        eqMatch = pd.concat([entityMatches, propertyMatches], ignore_index=True)
        # print(eqMatch)
        q = """SELECT
            l.*, r.gAnnotId as gSrc
            FROM
            subHasQuant l
            LEFT JOIN
            eqMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.src = r.annotId)
                WHERE r.docId not NULL"""
        env = {
            "subHasQuant":subHasQuant,
            "eqMatch":eqMatch
        }
        subHasQuant1 = sqldf(q, env)

        q = """SELECT
            l.*, r.gAnnotId as gTarget
            FROM
            subHasQuant1 l
            LEFT JOIN
            quantityMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.target = r.annotId)
                WHERE r.docId not NULL"""
        env = {
            "subHasQuant1":subHasQuant1,
            "quantityMatches":quantityMatches
        }
        subHasQuant2 = sqldf(q, env)

        q = """SELECT
            s.*
            FROM
            subHasQuant2 s
            JOIN
            goldHasQuant g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND s.relType = g.relType
                AND s.gSrc = g.src
                AND s.gTarget = g.target)"""

        # EM and F1 here are both binary (no partial overlap matches)
        env = {
            "subHasQuant2":subHasQuant2,
            "goldHasQuant":goldHasQuant
        }
        hasQuantMatch = sqldf(q, env)
        hasQuantMatch['EM'] = hasQuantMatch.apply (lambda x: 1.0, axis = 1 )
        hasQuantMatch['F1'] = None
        #print(hasQuantMatch)

        # As usual, we have both our Gold only and Submission only data.
        q = """SELECT
            l.*
            FROM
            subHasQuant l
            LEFT JOIN
            hasQuantMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.AnnotSet
                AND l.src = r.src)
                WHERE r.docId is NULL"""
        env = {
            "subHasQuant":subHasQuant,
            "hasQuantMatch":hasQuantMatch
        }
        subOnlyHasQuant = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldHasQuant l
            LEFT JOIN
            hasQuantMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.src = r.gSrc)
                WHERE r.docId is NULL"""
        env = {
            "goldHasQuant":goldHasQuant,
            "hasQuantMatch":hasQuantMatch
        }
        goldOnlyHasQuant = sqldf(q, env)

        # Do the same thing for HasProperty
        # Has property is always from a MeasuredEntity to a MeasuredProperty
        goldHasProp = goldRels.loc[goldRels["relType"] == "HasProperty"]
        subHasProp = subRels.loc[subRels["relType"] == "HasProperty"]

        q = """SELECT
            l.*, r.gAnnotId as gSrc
            FROM
            subHasProp l
            LEFT JOIN
            entityMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.src = r.annotId)
                WHERE r.docId not NULL"""
        env = {
            "subHasProp":subHasProp,
            "entityMatches":entityMatches
        }
        subHasProp1 = sqldf(q, env)

        q = """SELECT
            l.*, r.gAnnotId as gTarget
            FROM
            subHasProp1 l
            LEFT JOIN
            propertyMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.target = r.annotId)
                WHERE r.docId not NULL"""
        env = {
            "subHasProp1":subHasProp1,
            "propertyMatches":propertyMatches
        }
        subHasProp2 = sqldf(q, env)

        q = """SELECT
            s.*
            FROM
            subHasProp2 s
            JOIN
            goldHasProp g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND s.relType = g.relType
                AND s.gSrc = g.src
                AND s.gTarget = g.target)"""
        env = {
            "subHasProp2":subHasProp2,
            "goldHasProp":goldHasProp
        }
        hasPropMatch = sqldf(q, env)

        # EM and F1 here are both binary (no partial overlap matches)
        hasPropMatch['EM'] = hasPropMatch.apply (lambda x: 1.0, axis = 1 )
        hasPropMatch['F1'] = None

        # As usual, we have both our Gold only and Submission only data.
        q = """SELECT
            l.*
            FROM
            subHasProp l
            LEFT JOIN
            hasPropMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.AnnotSet
                AND l.src = r.src)
                WHERE r.docId is NULL"""
        env = {
            "subHasProp":subHasProp,
            "hasPropMatch":hasPropMatch
        }
        subOnlyHasProp = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldHasProp l
            LEFT JOIN
            hasPropMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.src = r.gSrc)
                WHERE r.docId is NULL"""
        env = {
            "goldHasProp":goldHasProp,
            "hasPropMatch":hasPropMatch
        }
        goldOnlyHasProp = sqldf(q, env)

        # Processing "Qualifies" Relationships
        # Source here is always a Qualifier
        # Target can be  any of entities, properties, or quantities
        # TODO: We had some cases where a qualifier could qualify a qualifier
        # Make sure these are gone. :)

        goldQualifies = goldRels.loc[goldRels["relType"] == "Qualifies"]
        subQualifies = subRels.loc[subRels["relType"] == "Qualifies"]

        destMatch = pd.concat([entityMatches, propertyMatches, quantityMatches], ignore_index=True)

        q = """SELECT
            l.*, r.gAnnotId as gSrc, r.EM, r.F1, r.maxF1
            FROM
            subQualifies l
            LEFT JOIN
            qualifierMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.src = r.annotId)
                WHERE r.docId not NULL"""
        env = {
            "subQualifies":subQualifies,
            "qualifierMatches":qualifierMatches
            
        }
        subQualifies1 = sqldf(q, env)

        q = """SELECT
            l.*, r.gAnnotId as gTarget
            FROM
            subQualifies1 l
            LEFT JOIN
            destMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.annotSet
                AND l.target = r.annotId)
                WHERE r.docId not NULL"""
        env = {
            "subQualifies1":subQualifies1,
            "destMatch":destMatch
        }
        subQualifies2 = sqldf(q, env)

        q = """SELECT
            s.*
            FROM
            subQualifies2 s
            JOIN
            goldQualifies g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND s.relType = g.relType
                AND s.gSrc = g.src
                AND s.gTarget = g.target)"""
        env = {
            "subQualifies2":subQualifies2,
            "goldQualifies":goldQualifies
        }
        qualifiesMatch = sqldf(q, env)

        # EM and F1 here are both binary (no partial overlap matches)
        qualifiesMatch['EM'] = qualifiesMatch.apply (lambda x: 1.0, axis = 1 )
        qualifiesMatch['F1'] = None

        # As usual, we have both our Gold only and Submission only data.
        q = """SELECT
            l.*
            FROM
            subQualifies l
            LEFT JOIN
            qualifiesMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.AnnotSet
                AND l.src = r.src)
                WHERE r.docId is NULL"""
        env = {
            "subQualifies":subQualifies,
            "qualifiesMatch":qualifiesMatch
        }
        subOnlyQualifies = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldQualifies l
            LEFT JOIN
            qualifiesMatch r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.src = r.gSrc)
                WHERE r.docId is NULL"""
        env = {
            "goldQualifies":goldQualifies,
            "qualifiesMatch":qualifiesMatch
        }
        goldOnlyQualifies = sqldf(q, env)

        # Final component are our modifiers.
        # there can be more than one modifier per Quantity
        # Note the use of "explodes" -- this requires Pandas >= 1.0.
        # Pulling these again out of the "other" data, and processing the json
        goldMods = goldQuants[goldQuants.other.notnull()].copy()
        goldMods['json'] = goldMods.apply (lambda x: json.loads(str(x.other)) if str(x.other) != "nan" else "", axis = 1 )
        goldMods['mods'] = goldMods.apply (lambda x: x.json["mods"] if "mods" in x.json.keys() else "", axis = 1)

        goldMods = goldMods.explode('mods')
        goldMods = goldMods[goldMods.mods != ""][["docId", "annotSet", "annotType", "startOffset", "endOffset", "annotId", "text", "mods", "EM", "F1", "maxF1"]]

        subMods = sub[sub["annotType"] == "Quantity"].copy()
        subMods = subMods[subMods.other.notnull()]
        subMods['json'] = None
        subMods['mods'] = None
        if not subMods.empty:
            subMods['json'] = subMods.apply (lambda x: json.loads(str(x.other)) if str(x.other) != "nan" else "", axis = 1 )
            subMods['mods'] = subMods.apply (lambda x: x.json["mods"] if "mods" in x.json.keys() else "", axis = 1)

        subMods = subMods.explode('mods')
        subMods = subMods[subMods.mods != ""][["docId", "annotSet", "gAnnotSet", "annotType", "startOffset", "endOffset", "annotId", "text", "mods", "EM", "F1", "maxF1"]]

        q = """SELECT
            s.gAnnotSet as matchAnnotSet, g.annotSet as gAnnotSet, s.docId, s.annotType, s.annotId,
            g.annotId as gAnnotId, s.startOffset, s.endOffset, s.text as sText, g.text as gText,
            s.mods as sMods, g.mods as gMods, s.EM, s.F1, s.maxF1
            FROM
            subMods s
            JOIN
            goldMods g
                ON (s.docId = g.docId
                AND s.gAnnotSet = g.annotSet
                AND s.mods = g.mods)"""
        env = {
            "subMods":subMods,
            "goldMods":goldMods
        }
        modsMatches = sqldf(q, env)
        modsMatches['EM'] = modsMatches.apply (lambda x: 1.0, axis = 1 )

        q = """SELECT
            l.*
            FROM
            subMods l
            LEFT JOIN
            modsMatches r
                ON (l.docId = r.docId
                AND l.gAnnotSet = r.gAnnotSet
                AND l.mods = r.sMods)
                WHERE r.docId is NULL"""
        env = {
            "subMods":subMods,
            "modsMatches":modsMatches
        }
        subOnlyMods = sqldf(q, env)

        q = """SELECT
            l.*
            FROM
            goldMods l
            LEFT JOIN
            modsMatches r
                ON (l.docId = r.docId
                AND l.annotSet = r.gAnnotSet
                AND l.mods = r.gMods)
                WHERE r.docId is NULL"""
        env = {
            "goldMods":goldMods,
            "modsMatches":modsMatches
        }
        goldOnlyMods = sqldf(q, env)

        # Penalty is defined as 0
        # This is where we apply the EM and F1 of 0 to all of our sub only and gold only results
        # We will also apply annotTypes to data that don't already have one
        # And we'll apply match types of "Match", "Gold only", and Sub only
        # These match types allow us to calculate precision, recall, and F1 for teh overall scores
        # Or at the document level or "class" level per the mode the evaluation script runs in.

        penalty = 0

        quantityMatches["annotType"] = quantityMatches.apply (lambda x: "Quantity", axis = 1 )
        quantityMatches["matchType"] = quantityMatches.apply (lambda x: "Match", axis = 1 )
        subOnlyQuants["EM"] = subOnlyQuants.apply (lambda x: penalty, axis = 1)
        subOnlyQuants["F1"] = subOnlyQuants.apply (lambda x: penalty, axis = 1)
        subOnlyQuants["matchType"] = subOnlyQuants.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyQuants["EM"] = goldOnlyQuants.apply (lambda x: penalty, axis = 1)
        goldOnlyQuants["F1"] = goldOnlyQuants.apply (lambda x: penalty, axis = 1)
        goldOnlyQuants["matchType"] = goldOnlyQuants.apply (lambda x: "Gold only", axis = 1 )

        unitMatches["annotType"] = unitMatches.apply (lambda x: "Unit", axis = 1)
        unitMatches["matchType"] = unitMatches.apply (lambda x: "Match", axis = 1 )
        subOnlyUnits["annotType"] = subOnlyUnits.apply (lambda x: "Unit", axis = 1)
        goldOnlyUnits["annotType"] = goldOnlyUnits.apply (lambda x: "Unit", axis = 1)
        subOnlyUnits["EM"] = subOnlyUnits.apply (lambda x: penalty, axis = 1)
        subOnlyUnits["F1"] = subOnlyUnits.apply (lambda x: penalty, axis = 1)
        subOnlyUnits["matchType"] = subOnlyUnits.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyUnits["EM"] = goldOnlyUnits.apply (lambda x: penalty, axis = 1)
        goldOnlyUnits["F1"] = goldOnlyUnits.apply (lambda x: penalty, axis = 1)
        goldOnlyUnits["matchType"] = goldOnlyUnits.apply (lambda x: "Gold only", axis = 1 )
        goldOnlyUnits["matchType"] = goldOnlyUnits.apply (lambda x: "Gold only", axis = 1 )

        entityMatches["matchType"] = entityMatches.apply (lambda x: "Match", axis = 1 )
        subOnlyEntities["EM"] = subOnlyEntities.apply (lambda x: penalty, axis = 1)
        subOnlyEntities["F1"] = subOnlyEntities.apply (lambda x: penalty, axis = 1)
        subOnlyEntities["matchType"] = subOnlyEntities.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyEntities["EM"] = goldOnlyEntities.apply (lambda x: penalty, axis = 1)
        goldOnlyEntities["F1"] = goldOnlyEntities.apply (lambda x: penalty, axis = 1)
        goldOnlyEntities["matchType"] = goldOnlyEntities.apply (lambda x: "Gold only", axis = 1 )

        propertyMatches["matchType"] = propertyMatches.apply (lambda x: "Match", axis = 1 )
        subOnlyProperties["EM"] = subOnlyProperties.apply (lambda x: penalty, axis = 1)
        subOnlyProperties["F1"] = subOnlyProperties.apply (lambda x: penalty, axis = 1)
        subOnlyProperties["matchType"] = subOnlyProperties.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyProperties["EM"] = goldOnlyProperties.apply (lambda x: penalty, axis = 1)
        goldOnlyProperties["F1"] = goldOnlyProperties.apply (lambda x: penalty, axis = 1)
        goldOnlyProperties["matchType"] = goldOnlyProperties.apply (lambda x: "Gold only", axis = 1 )

        qualifierMatches["matchType"] = qualifierMatches.apply (lambda x: "Match", axis = 1 )
        subOnlyQualifiers["EM"] = subOnlyQualifiers.apply (lambda x: penalty, axis = 1)
        subOnlyQualifiers["F1"] = subOnlyQualifiers.apply (lambda x: penalty, axis = 1)
        subOnlyQualifiers["matchType"] = subOnlyQualifiers.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyQualifiers["EM"] = goldOnlyQualifiers.apply (lambda x: penalty, axis = 1)
        goldOnlyQualifiers["F1"] = goldOnlyQualifiers.apply (lambda x: penalty, axis = 1)
        goldOnlyQualifiers["matchType"] = goldOnlyQualifiers.apply (lambda x: "Gold only", axis = 1 )

        hasQuantMatch["matchType"] = hasQuantMatch.apply (lambda x: "Match", axis = 1 )
        hasQuantMatch["F1"] = hasQuantMatch.apply (lambda x: x.EM, axis = 1)
        subOnlyHasQuant["EM"] = subOnlyHasQuant.apply (lambda x: penalty, axis = 1)
        subOnlyHasQuant["F1"] = subOnlyHasQuant.apply (lambda x: penalty, axis = 1)
        subOnlyHasQuant["matchType"] = subOnlyHasQuant.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyHasQuant["EM"] = goldOnlyHasQuant.apply (lambda x: penalty, axis = 1)
        goldOnlyHasQuant["F1"] = goldOnlyHasQuant.apply (lambda x: penalty, axis = 1)
        goldOnlyHasQuant["matchType"] = goldOnlyHasQuant.apply (lambda x: "Gold only", axis = 1 )

        hasPropMatch["matchType"] = hasPropMatch.apply (lambda x: "Match", axis = 1 )
        hasPropMatch["F1"] = hasPropMatch.apply (lambda x: x.EM, axis = 1)
        subOnlyHasProp["EM"] = subOnlyHasProp.apply (lambda x: penalty, axis = 1)
        subOnlyHasProp["F1"] = subOnlyHasProp.apply (lambda x: penalty, axis = 1)
        subOnlyHasProp["matchType"] = subOnlyHasProp.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyHasProp["EM"] = goldOnlyHasProp.apply (lambda x: penalty, axis = 1)
        goldOnlyHasProp["F1"] = goldOnlyHasProp.apply (lambda x: penalty, axis = 1)
        goldOnlyHasProp["matchType"] = goldOnlyHasProp.apply (lambda x: "Gold only", axis = 1 )

        qualifiesMatch["matchType"] = qualifiesMatch.apply (lambda x: "Match", axis = 1 )
        #print(qualifiesMatch)
        qualifiesMatch["F1"] = qualifiesMatch.apply (lambda x: x.EM, axis = 1)
        subOnlyQualifies["EM"] = subOnlyQualifies.apply (lambda x: penalty, axis = 1)
        subOnlyQualifies["F1"] = subOnlyQualifies.apply (lambda x: penalty, axis = 1)
        subOnlyQualifies["matchType"] = subOnlyQualifies.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyQualifies["EM"] = goldOnlyQualifies.apply (lambda x: penalty, axis = 1)
        goldOnlyQualifies["F1"] = goldOnlyQualifies.apply (lambda x: penalty, axis = 1)
        goldOnlyQualifies["matchType"] = goldOnlyQualifies.apply (lambda x: "Gold only", axis = 1 )

        modsMatches["matchType"] = modsMatches.apply (lambda x: "Match", axis = 1 )
        modsMatches["F1"] = modsMatches.apply (lambda x: x.EM, axis = 1)
        subOnlyMods["EM"] = subOnlyMods.apply (lambda x: penalty, axis = 1)
        subOnlyMods["F1"] = subOnlyMods.apply (lambda x: penalty, axis = 1)
        subOnlyMods["matchType"] = subOnlyMods.apply (lambda x: "Sub only", axis = 1 )
        goldOnlyMods["EM"] = goldOnlyMods.apply (lambda x: penalty, axis = 1)
        goldOnlyMods["F1"] = goldOnlyMods.apply (lambda x: penalty, axis = 1)
        goldOnlyMods["matchType"] = goldOnlyMods.apply (lambda x: "Gold only", axis = 1 )
        modsMatches["relType"] = modsMatches.apply (lambda x: "modifier", axis = 1)
        subOnlyMods["relType"] = subOnlyMods.apply (lambda x: "modifier", axis = 1)
        goldOnlyMods["relType"] = goldOnlyMods.apply (lambda x: "modifier", axis = 1)

        # Concatenate the whole darn thing by building an array of these dataframes
        # Selecting the fields we need, and renaming columns as needed.
        wrk1array = [quantityMatches[["docId", "matchType", "annotType", "EM", "maxF1"]].rename(columns={"maxF1":"F1", "annotType":"type"}),
                    subOnlyQuants[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    goldOnlyQuants[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    unitMatches[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    subOnlyUnits[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    goldOnlyUnits[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    entityMatches[["docId", "matchType", "annotType", "EM", "maxF1"]].rename(columns={"maxF1":"F1", "annotType":"type"}),
                    subOnlyEntities[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    goldOnlyEntities[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    propertyMatches[["docId", "matchType", "annotType", "EM", "maxF1"]].rename(columns={"maxF1":"F1", "annotType":"type"}),
                    subOnlyProperties[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    goldOnlyProperties[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    qualifierMatches[["docId", "matchType", "annotType", "EM", "maxF1"]].rename(columns={"maxF1":"F1", "annotType":"type"}),
                    subOnlyQualifiers[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    goldOnlyQualifiers[["docId", "matchType", "annotType", "EM", "F1"]].rename(columns={"annotType":"type"}),
                    hasQuantMatch[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    subOnlyHasQuant[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    goldOnlyHasQuant[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    hasPropMatch[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    subOnlyHasProp[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    goldOnlyHasProp[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    qualifiesMatch[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    subOnlyQualifies[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    goldOnlyQualifies[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    modsMatches[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    subOnlyMods[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"}),
                    goldOnlyMods[["docId", "matchType", "relType", "EM", "F1"]].rename(columns={"relType":"type"})
                    ]

        # Now we'll concatenate that into the final scoring dataframe.
        wrk1score = pd.concat(wrk1array, ignore_index=True)


        # Recall from the arguments, we have modes in which this scoring is run.
        # That determines how averages are calculated.
        # The default is "overall", which averages everything.
        # The overall F1 is the score used on the leaderboard.

        #parser.add_argument('-m', '--mode', help='Mode to run scoring: overall, class, doc, or both; default is overall.', default="overall")

        # In overall mode, we count true positives, false positives, and false negatives
        # From the Match, Sub only, and Gold only sets.
        # We use this to determine a precision and recall, as well as an F-measure
        # Finally, we give you your overall EM and Overlap score.
        # print(wrk1score.shape)
        # print(wrk1score.columns)

        cats = {}
        filecats = open("/home/huangruijun/grpo/utils/fileCategories.txt", "r")
        lines = filecats.readlines()
        for line in lines:
            cats[line.split('\t')[0]] = line.split('\t')[1].rstrip()
        filecats.close()

        wrk1score["subject"] = wrk1score.apply (lambda x: cats[x['docId'].split("-")[0]], axis = 1)

        # for index, row in wrk1score.iterrows():
        #     print(row['docId'].split('-')[0])
        #     print(cats[row['docId'].split('-')[0]])
        #     print(row['subject'].split('-')[0])
        tp = len(wrk1score.loc[wrk1score["matchType"] == "Match"].index)
        fp = len(wrk1score.loc[wrk1score["matchType"] == "Sub only"].index)
        fn = len(wrk1score.loc[wrk1score["matchType"] == "Gold only"].index)
        # print("True positives (matching rows): " + str(tp))
        # print("False positives (submission only): " + str(fp))
        # print("False negatives (gold only): " + str(fn))
        print("")
        if tp+fp == 0:
            print("Submission has no data.")
            print("")
        elif tp == 0:
            print("Submission has no matches against gold data")
        else:
            precision = tp / (tp+fp)
            recall = tp / (tp + fn)
            fmeas = (2 * precision * recall) / (precision + recall)

            # print("Precision: " + str(precision))
            # print("Recall: " + str(recall))
            # print("F-measure: " + str(fmeas))
            # print("")

        # print("Overall Score Exact Match: " + str(wrk1score["EM"].mean()))
        # print("Overall Score F1 (Overlap): " + str(wrk1score["F1"].mean()))
        # return wrk1score["F1"].mean() * 3 - penalty
        score = 0
        penal = 0
        penal2 = 0
        for annotType in (["Quantity"]):
            # print("Processing " + annotType)
            tp = len(wrk1score.loc[((wrk1score["matchType"] == "Match") &
                                    (wrk1score["type"] == annotType))].index)
            fp = len(wrk1score.loc[((wrk1score["matchType"] == "Sub only") &
                                    (wrk1score["type"] == annotType))].index)
            fn = len(wrk1score.loc[((wrk1score["matchType"] == "Gold only") &
                                    (wrk1score["type"] == annotType))].index)
            if tp+fp == 0:
                print("Submission has no data for " + annotType)
                # print("")
            elif tp == 0:
                print("Submission has no matches against gold data for " + annotType)
            else:
                # print("True positives (matching rows) for " + annotType + ": " + str(tp))
                # print("False positives (submission only) for " + annotType + ": " + str(fp))
                # print("False negatives (gold only) for " + annotType + ": " + str(fn))
                # print("")
                precision = tp / (tp+fp)
                # print("Precision for " + annotType + ": " + str(precision))
                recall = tp / (tp + fn)
                # print("Recall for " + annotType + ": " + str(recall))
                fmeas = (2 * precision * recall) / (precision + recall)
                # print("F-measure for " + annotType + ": " + str(fmeas))
                # print("")
                penal += 1-precision
                penal2 += 1-recall
            # print("Exact Match Score for " + annotType + ": " +
                # str(wrk1score.loc[wrk1score["type"] == annotType]["EM"].mean()))
            # print("F1 (Overlap) Score for " + annotType + ": " +
                # str(wrk1score.loc[wrk1score["type"] == annotType]["F1"].mean()))
            # print("")
            t= wrk1score.loc[wrk1score["type"] == annotType]["F1"].mean()
            if pd.isna(t):
                score += 0
            else:
                score +=t
        return score*10.0 - 100 * penal
   except Exception as e:
        # print(sub)
        traceback.print_exc()
        return -10000