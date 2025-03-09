## Start Grobit Quantities Docker Server

```shell
docker run --rm --init -p 8060:8060 -p 8061:8061 -v config/config-docker.yml:/opt/grobid/grobid-quantities/resources/config/config.yml:ro lfoppiano/grobid-quantities:0.8.0
```

# Call the API 

```shell
curl --form input=@./Documents/微纳智造/ahmadi2012\ hydrothermal.pdf localhost:8060/service/annotateQuantityPDF
```