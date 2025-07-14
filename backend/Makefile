# Makefile backend

LAMBDA_NAME = todaslascasas-api-dev-api
ZIP_NAME = lambda.zip

build:
	@echo "⏳ Empaquetando Lambda…"
	zip -r $(ZIP_NAME) ../lambda-package-complete/lambda_function.py ../lambda-package-complete/api_postgresql.py ../lambda-package-complete/lambda_build -x "*__pycache__*" "*.pyc" > /dev/null
	@du -h $(ZIP_NAME)

clean:
	@rm -f $(ZIP_NAME)

deploy-stg: build
	@echo "🚀 Desplegando a alias stg…"
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(ZIP_NAME) --publish
	aws lambda update-alias --function-name $(LAMBDA_NAME) --name stg --function-version `aws lambda list-versions-by-function --function-name $(LAMBDA_NAME) --max-items 1 --query 'Versions[0].Version' --output text`

deploy-prod:
	@echo "🚀 Desplegando a prod (alias live)…"
	aws lambda update-alias --function-name $(LAMBDA_NAME) --name live --function-version `aws lambda list-versions-by-function --function-name $(LAMBDA_NAME) --max-items 1 --query 'Versions[0].Version' --output text` 