#/bin/bash

#Python2 is a piece of crap that won't work with Unicode paths
#So I create a pseudo-deployment with symlinks in /tmp

TEMP_DIR_PATH=" /tmp/PolyglotGroupBot"

mkdir $TEMP_DIR_PATH

#Files to link to pseudo-deployment folder. First, fetch all Git-tracked ones 
FILES=( $(git ls-tree -r master --name-only) )
FILES+=('token.txt')

lns(){ ln -s $(realpath $1) $(realpath $2); }

for i in "${FILES[@]}"
do
	lns $i $TEMP_DIR_PATH
done



exit 0