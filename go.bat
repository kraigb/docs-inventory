pushd ..\visualstudio-docs-pr
git pull origin master
cd ..\vscode-docs
git pull origin master
cd ..\vsts-docs-pr
git pull origin master
cd ..\azure-docs-sdk-java
git pull origin master
cd ..\azure-docs-sdk-python
git pull origin master
cd ..\azure-docs-sdk-node
git pull origin master
cd ..\azure-docs-pr
git pull origin master
popd
python take_inventory.py
