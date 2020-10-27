set +x
mkdir -p functions/packages
for i in functions/source/*; do base=$(basename "$i"); cd $i; zip -r "$base.zip" . ; mv $base.zip ../../packages/; cd -; done
