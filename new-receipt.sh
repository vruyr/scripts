#!/usr/bin/env bash

file_dir="$HOME/Downloads"
file_base_name="receipt"
file_path="${file_dir}/${file_base_name}.txt"
declare -i counter=0
while [ -e "${file_path}" ]; do
	counter=$(( counter + 1 ))
	file_path="${file_dir}/${file_base_name}-${counter}.txt"
done

file_path="${file_path}"
echo $file_path

cat >"$file_path" <<-EOT
	Transaction Date:
	Location:
	Account:
	Payee:
	Amount:
EOT


$(git var GIT_EDITOR) "$file_path"
