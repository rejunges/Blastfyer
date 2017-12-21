# Blastfyer
The Blastfyer program is a tool to distribute activities from BLAST (Basic Local Alignment Search Tool), through several computers, speeding up the execution velocity. Blastfyer was complete developed on python 3 and execute in a client-server network, then there is a folder with client program and other folder with the server program.

## Prerequisites
* Python 3
* BLAST
* FTP Server (to download necessary .fasta files and upload output files)

## Commands

### Server:

To start the server, you need to type the Blastfyer mandatory parameter:

* **ftp**: ftp address of blast files to be executed
* other required options may vary with the BLAST family of programs. 

```
python3 server.py -ftp login:pass@123.123.123.123 -query folder/path.fasta another_folder/file/*.fasta -db path/database.fasta -out output/file -outfmt 5
```

Note that you can add other BLAST options when running the server. To see a complete list of options, please visit session 4.6: http://nebc.nerc.ac.uk/bioinformatics/documentation/blast+/user_manual.pdf

### Client:

For each client computer, you need the required Blastfyer option:
* **host**: ip address of client server

Optional parameters:

* **port**: available server port
* **num_threads**: number of threads used to BLAST execution
```
python3 client.py -host 255.255.255.255
```

If you’re not sure how to use a specific BLAST command, run: 


```
python3 client.py -h
```

## Contact
* [Renata Junges](https://github.com/rejunges)
* [Lúcio Leal](https://github.com/llbastos)
