# -- test bash script in qq_test_one bin
qunex whoisonone

# -- test matlab
qunex g_greetings

quenx g_greetings --name=Grega

# -- test python command
qunex print_hello 

qunex print_hello --name=Grega

# -- test python processing command
qunex greet_all \
    --sessions=/gpfs/gibbs/pi/n3/Studies/MBLab/sWM/processing/batch.txt \
	--sessionsfolder=/gpfs/gibbs/pi/n3/Studies/MBLab/sWM/subjects \
	--p_name=Grega