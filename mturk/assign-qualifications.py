from boto.mturk.connection import MTurkConnection, MTurkRequestError
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
import os

key_file = 'mturk/aws-key.txt'
assert os.path.exists(key_file), 'Remember to save your access key into %s' %key_file
with open(key_file) as f:
    keys = dict(line.strip().split('=') for line in f)
requester_host = 'mechanicalturk.amazonaws.com'

class Pair1Q:
    keyword = '#P1Q'
    qualification = '3I79FTN7D30DE2C4E07NA8PVV4P4EG'
    workers = set()

class Pair2Q:
    keyword = '#P2Q'
    qualification = '32S8022MNQ8RK8MWVMURN3FF41QL4K'
    workers = set()

class Chunk5S:
    keyword = '#C5S'
    qualification = '3HNFI9Q0TBC7NREQREOYUT58VHP73C'
    workers = set()

class Chunk10S:
    keyword = '#C10S'
    qualification = '303SJT1CWD55KGC09BRTSQAV7544FY'
    workers = set()

class DocumentDesign:
    keyword = '#DOC'
    qualification = '33LK213QXTE569FOG685NNQX6KUCQD'
    workers = set()
    
BadAnnotatorQualification = '36F71BC7TI1S5NXURSTH4YXE9HL74X'

designs = [Pair1Q, Pair2Q, Chunk5S, Chunk10S, DocumentDesign]

if __name__ == '__main__':
    conn = MTurkConnection(aws_access_key_id=keys['AWSAccessKeyId'],
                           aws_secret_access_key=keys['AWSSecretKey'],
                           host=requester_host)
    i = 1
    while True:
        hits = conn.search_hits(page_size=100, page_number=i)
        if not hits: break
        for h in hits:
            for dsg in designs:
                if dsg.keyword in h.Title:
                    for a in conn.get_assignments(h.HITId):
                        dsg.workers.add(a.WorkerId)
        i += 1

    for dsg in designs:
        for worker in dsg.workers:
            try:
                conn.assign_qualification(qualification_type_id=dsg.qualification, 
                                          worker_id=worker, send_notification=False)
            except MTurkRequestError:
                pass
            
    #TODO bad annotator