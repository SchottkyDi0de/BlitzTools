$ROOT_CLASS_NAME = "ConfigStruct"
$INPUT_FILE_TYPE = "yaml"
$PROJECT_PATH = Split-Path -Path $PSScriptRoot -Parent
$PATH_TO_INPUT_FILE = Join-Path -Path $PROJECT_PATH -ChildPath "/config/default_config.yaml"
$OUTPUT_FILE_PATH = Join-Path -Path $PROJECT_PATH -ChildPath "/lib/dataclasses/configs/main_config.py"
$MODEL_TYPE = "pydantic_v2.BaseModel"
$ENCODING = "utf-8"

datamodel-codegen --input $PATH_TO_INPUT_FILE --input-file-type $INPUT_FILE_TYPE --output $OUTPUT_FILE_PATH --output-model-type $MODEL_TYPE --class-name $ROOT_CLASS_NAME --disable-future-imports --encoding $ENCODING
Write-Output "Datamodel code generated in $OUTPUT_FILE_PATH"
