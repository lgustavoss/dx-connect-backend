Param(
  [string]$Folder = ""
)

$collection = ".postman/DX Connect API.postman_collection.json"
$envFile    = ".postman/DX Connect Local.postman_environment.json"

if ([string]::IsNullOrWhiteSpace($Folder)) {
  npx --yes newman run $collection -e $envFile
} else {
  npx --yes newman run $collection -e $envFile --folder $Folder
}


