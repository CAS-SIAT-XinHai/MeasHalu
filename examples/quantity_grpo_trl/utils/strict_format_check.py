import re
def strict_check(input):
    pattern = r"^<ARABIC-QUANTITY>.*</ARABIC-QUANTITY>\n+<ALPHABETIC-QUANTITY>.*</ALPHABETIC-QUANTITY>\n+<CHANGE-QUANTITY>.*</CHANGE-QUANTITY>\n+<TIME-QUANTITY>.*</TIME-QUANTITY>\n+<FORMULA-QUANTITY>.*</FORMULA-QUANTITY>\n+<CONCLUSION>.*</CONCLUSION>$"
    match = re.search(pattern, input, re.DOTALL)
    if match != None:
        return 1.0
    else:
        # print("strict_check------------------------------------------------")
        # print(match)
        # print(input)
        # print("--------------------------------------------------------------")
        return 0.0