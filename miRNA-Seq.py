from pyrpipe import sra,qc
import glob
import pandas as pd
from pandas import DataFrame





#Output directory
DIR='output'
#creates a trim_galore object.
trim_galore=qc.Trimgalore(threads=4)

#Read in run accession IDs from txt file.
with open ("RAids.txt") as f:
    ra=f.read().splitlines()


rule all:
        input: "countTable.tsv"

rule miRNA_Quant:
    output:
        "{wd}/{sample}/miRNAs_expressed_all_samples_{sample}.csv"
    run:
        #Make variable for raid and pathway to corresponding directory.
        raid=str({output}).split("/")[1]  
        path=DIR+"/"+raid + "/"      
        #Download fastq(s) from SRA. Run through trim_galore
        sra.SRA(raid,directory=DIR).trim(trim_galore)               
        #Processes reads for quantification 
        shell("mapper.pl "+ path + raid + "_1_trimgalore.fastq  -e -m -h \
            -g " + raid[-3:] + " \
            -s " + path + raid + ".fasta")
        #Quantification 
        shell("quantifier.pl \
            -p hairpin.fa \
            -m mature.fa \
            -r " + path + raid + ".fasta \
            -y " + raid + " \
            -t rno")
            
        #Move output
        shell("mv *" + raid + "* " + path)

rule Count_Table:
    input:
        ["{wd}/{sample}/miRNAs_expressed_all_samples_{sample}.csv".format(wd=DIR,sample=s) for s in ra]
    output:
        "countTable.tsv"
    run:           
        x=0
        for qf in input:
            raid=qf.split('/')[1] 
            path=DIR+"/"+raid + "/"        
            #Read in miRNAs_expressed_all_samples_{sample}.csv 
            quant_df=pd.read_csv(path+"miRNAs_expressed_all_samples_"+raid+".csv",sep="\t")  
            # Get #miRNA  and precursor IDs from miRNAs_expressed_all_samples_{sample}.csv
            if x==0:                
                countTable=quant_df[["#miRNA","precursor"]]
                countTable = countTable.rename(columns={'#miRNA': 'miRNA'})                                                     
                x=1
             # Extract counts then add to table.               
            countTable[raid]=quant_df[raid[-3:]]
        #Mature miRNA's can have more than 1 precursor. For this type of mature miRNA, this takes the average across precursors. 
        countTable = countTable.groupby(['miRNA'],as_index = False).mean()  
        countTable.to_csv("countTable.tsv",mode="w", header=True,index=False,sep="\t")
