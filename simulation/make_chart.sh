#!/bin/bash

for i in `seq 1 1000`; do
	./wymiennik 1
	cat heat_exchanger_data.txt | sed -n '5p' >> heat_exchanger_tpm.txt
	cat heat_exchanger_data.txt | sed -n '6p' >> heat_exchanger_tzco.txt
done
