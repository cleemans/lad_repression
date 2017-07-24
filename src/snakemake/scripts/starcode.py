import subprocess
import re

count_file = snakemake.input[0]
use_other = snakemake.params.use_other
if use_other:
    starcode_file = snakemake.input[1]
    with open(starcode_file) as f:
        barcode_set = set()
        for line in f.readlines():
            line_strip = line.strip().split('\t')
            barcode_set.add(line_strip[0])
    stdin = ['%s\t10000' % barcode for barcode in barcode_set]
else:
    stdin = []

count_dict = {}
with open(count_file) as f:
    for line in f.readlines():
        line_split = line.strip().split()
        barcode = line_split[0]
        count_dict[barcode] = int(line_split[1])
        if not use_other:
            stdin.append(line)
        elif barcode not in barcode_set:
            stdin.append('%s\t1' % barcode)


args = ('/home/NFS/users/c.leemans/Programs/starcode/starcode'
        ' --print-clusters -d %i -t %i -s' % (snakemake.params.lev_dist,
                                              snakemake.threads))

starcode = subprocess.Popen(args, shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    outs, errs = starcode.communicate(bytes('\n'.join(stdin), 'UTF-8'),
                                      timeout=15)
except subprocess.TimeoutExpired:
    starcode.kill()
    outs, errs = starcode.communicate()

genuine = open(snakemake.output.gen, 'w')
mutated = open(snakemake.output.mut, 'w')
count = open(snakemake.output.count, 'w')
if use_other:
    notg = open(snakemake.output.notg, 'w')
for line in outs.decode('UTF-8').split('\n'):
    line_split = line.split('\t')
    barcode = line_split[0]
    if barcode != '':
        if use_other and barcode not in barcode_set:
            notg.write('%s\t%i\n' % (barcode, count_dict[barcode]))
        elif barcode in count_dict:
            if count_dict[barcode] > snakemake.params.count:
                genuine.write('%s\t%i\n' % (barcode, count_dict[barcode]))
            else:
                count.write('%s\t%i\n' % (barcode, count_dict[barcode]))
            if use_other:
                barcode_set.remove(barcode)
        else:
            genuine.write('%s\t0\n' % barcode)
        if len(line_split) == 3:
            other_list = line_split[2].split(',')
            for other_barcode in other_list:
                if other_barcode != barcode:
                    mutated.write('%s\t%i\t%s\n' % (other_barcode,
                                                    count_dict[other_barcode],
                                                    barcode))
                    if use_other:
                        barcode_set.remove(other_barcode)

mutated.close()
genuine.close()
if use_other:
    with open(snakemake.output.notc, 'w') as notc:
        for barcode in barcode_set:
            notc.write(barcode)
            notc.write('\n')
    notg.close()
