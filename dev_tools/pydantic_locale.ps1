$ROOT_CLASS_NAME = "LocaleStruct"
$INPUT_FILE_TYPE = "yaml"
$PROJECT_PATH = Split-Path -Path $PSScriptRoot -Parent
$PATH_TO_INPUT_FILE = Join-Path -Path $PROJECT_PATH -ChildPath "locales/ru.yaml"
$OUTPUT_FILE_PATH = Join-Path -Path $PROJECT_PATH -ChildPath "lib/dataclasses/locale/struct.py"
$MODEL_TYPE = "pydantic_v2.BaseModel"
$ENCODING = "utf-8"

datamodel-codegen --input $PATH_TO_INPUT_FILE --input-file-type $INPUT_FILE_TYPE --output $OUTPUT_FILE_PATH --output-model-type $MODEL_TYPE --class-name $ROOT_CLASS_NAME --disable-future-imports --encoding $ENCODING
Write-Output "Data model code generated in $OUTPUT_FILE_PATH"
