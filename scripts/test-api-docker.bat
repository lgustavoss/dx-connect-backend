@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Usage:
REM   scripts\test-api-docker.bat
REM   scripts\test-api-docker.bat "Config Company - Patch"

set COLLECTION=DX Connect API.postman_collection.json
set ENVFILE=DX Connect Local.postman_environment.json

set FOLDER=%~1

set MOUNT="%CD%\.postman:/etc/newman"

if "%FOLDER%"=="" (
  docker run --rm -v %MOUNT% postman/newman run "%COLLECTION%" -e "%ENVFILE%" --env-var base_url=http://host.docker.internal:8001
) else (
  docker run --rm -v %MOUNT% postman/newman run "%COLLECTION%" -e "%ENVFILE%" --env-var base_url=http://host.docker.internal:8001 --folder "%FOLDER%"
)

endlocal

