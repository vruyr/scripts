#!/bin/zsh

set -euo pipefail

date_local=$(date +"%Y-%m-%d %H:%M:%S %z")

echo "# Apple Shortcuts Backup"
echo ""
echo "Backed up ${date_local}"

folders=("${(@f)$(shortcuts list --folders)}")

for folder in "${folders[@]}"; do
	[[ -z "$folder" ]] && continue
	echo ""
	echo ""
	echo "## ${folder}"
	echo ""
	items=("${(@f)$(shortcuts list --folder-name "$folder")}")
	i=1
	for item in "${items[@]}"; do
		[[ -z "$item" ]] && continue
		echo "${i}. ${item}"
		((i++))
	done
done

no_folder_items=("${(@f)$(shortcuts list --folder-name none)}")
if (( ${#no_folder_items[@]} > 0 )) && [[ -n "${no_folder_items[1]}" ]]; then
	echo ""
	echo ""
	echo "## Uncategorized"
	echo ""
	i=1
	for item in "${no_folder_items[@]}"; do
		[[ -z "$item" ]] && continue
		echo "${i}. ${item}"
		((i++))
	done
fi
