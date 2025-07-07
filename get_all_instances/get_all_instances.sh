#!/bin/bash
# Get the name of my tenancy
COMPARTMENT=$(oci iam user get --user-id "$(oci iam user list --all --query "data[0].id" --raw-output)" --query "data.\"compartment-id\"" --raw-output)
COMPARTMENT_NAME="$(oci iam compartment get --compartment-id ${COMPARTMENT} --query data.name --raw-output)"
# Build output file name
filename=${COMPARTMENT_NAME}_extraction_$(date +'%Y%m%d%H%M%S').csv

# Prepare output CSV
echo "Compartment Name,Compartment OCID,Instance Name,Instance OCID,Image OCID,Operating System,OS Version" > $filename 

# Get all active compartments
compartments=$(oci iam compartment list --compartment-id $COMPARTMENT \
  --compartment-id-in-subtree true --all \
  --query "data[?\"lifecycle-state\"=='ACTIVE'].[id,name]" \
  --output json)

# Loop through each compartment
echo "$compartments" | jq -c '.[]' | while read comp; do
  comp_id=$(echo "$comp" | jq -r '.[0]')
  comp_name=$(echo "$comp" | jq -r '.[1]')

  # List instances in the compartment
  instances=$(oci compute instance list --compartment-id "$comp_id" --all \
    --query "data[?\"lifecycle-state\"=='RUNNING' || \"lifecycle-state\"=='STOPPED']" \
    --output json)

  echo "$instances" | jq -c '.[]' | while read inst; do
    inst_name=$(echo "$inst" | jq -r '.["display-name"]')
    inst_ocid=$(echo "$inst" | jq -r '.id')
    image_ocid=$(echo "$inst" | jq -r '.["image-id"]')

    # Get image metadata to identify OS
    image_info=$(oci compute image get --image-id "$image_ocid" --query 'data' --output json)
    os_name=$(echo "$image_info" | jq -r '.["operating-system"]')
    os_version=$(echo "$image_info" | jq -r '.["operating-system-version"]')

    echo "$comp_name,$comp_id,$inst_name,$inst_ocid,$image_ocid,$os_name,$os_version" >> $filename
  done
done
