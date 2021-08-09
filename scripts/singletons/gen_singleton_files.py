''' Create a variation of CoNLL with singletons in each file
Usage:
    gen_singleton_files_1 <input_dir> <output_dir> <filetype (extension)>
'''
from utils import *

import os
import sys
import shutil

def main(inp_dir, out_dir, filetype="v4_gold_conll"):
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in os.listdir(inp_dir):
        if filename.split(".")[-1] != filetype:
            continue
        # else: file is a file that we want to convert
        filepath = inp_dir+"/"+filename
        out_path = out_dir+"/"+filename
        # check to see if corresponding html exists; if it does, copy it
        if os.path.isfile(filepath+".html"):
            shutil.copyfile(filepath+".html", out_path+".html")

        data = import_conll(filepath)
        final_mentions = extract_final_candidates(data)
        coref_info = get_coref_info(final_mentions)
        
        # Alters data itself, adding 'coref' to each line
        for sentence in data:
            for entry in sentence:
                file_id = entry["file_id"]
                sentence_id = entry["sent_id"]
                tok_id = entry["tok_id"]
                if (file_id, sentence_id, tok_id) in coref_info:
                    entry["coref"] = coref_info[(file_id, sentence_id, tok_id)]
                else:
                    if entry["coref"]!="-":
                        print(f"error at: {file_id, sentence_id, tok_id}. No mention string in coref_info.")
                        print(entry["coref"])
        write_conll(data, out_path)
    return


if __name__ == '__main__':
    args = sys.argv
    if len(args)==4:
         main(args[1], args[2], args[3])
    elif len(args)==3:
        main(args[1], args[2])
    else:
        print("Error: requires 2 arguments (input_dir, outpur_dir).")
        