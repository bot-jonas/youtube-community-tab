repo=$1
python3 -m twine upload --repository $repo dist/*
