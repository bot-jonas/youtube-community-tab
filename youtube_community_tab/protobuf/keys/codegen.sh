key_name=$1
python3 -m grpc_tools.protoc -I $key_name --python_out=$key_name $key_name/$key_name.proto
