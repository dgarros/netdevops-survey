import pandas as pd 
import base64 
import math
import argparse

def main():
    
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('--survey', action='store', type=int, required=True)
    my_parser.add_argument('--question', action='store', type=str, required=True)

    args = my_parser.parse_args()
    
    df = pd.read_csv(f'../results/{args.survey}.tsv', sep='\t', header=0) 

    responses = {}

    if args.question not in df.columns:
        print("ERROR: Unable to find the question in the document")
        exit(1)
    
    for resp in list(df[args.question]) :

        if not resp or (isinstance(resp, float) and math.isnan(resp)): 
            continue
        
        if isinstance(resp, str):
            values = resp.split(",")
        else:
            values = [str(resp)]

        for value in values:

            b64v = base64.encodebytes(value.strip().encode())

            if b64v not in responses.keys():
                responses[b64v] = 1
            else:
                responses[b64v] += 1

    tmp = [ { "resp": k, "count": v } for k,v in responses.items() ]
    sorted_resps = sorted(tmp, key = lambda i: i['count'], reverse=True) 
        
    for response in sorted_resps:
        print(f"{response['count']} - {base64.decodebytes(response['resp']).decode()}")

if __name__ == '__main__':
    main()
