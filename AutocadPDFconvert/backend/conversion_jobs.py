import uuid

jobs = {}  
# job_id: {
#    "files": [ {file, status}, ... ],
#    "zip_bytes": None,
#    "done": False
# }

def create_job(files):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "files": [{"file": f.filename, "status": "waiting"} for f in files],
        "zip_bytes": None,
        "done": False,
    }
    return job_id

def update_status(job_id, index, status):
    jobs[job_id]["files"][index]["status"] = status

def finish_job(job_id, zip_bytes):
    jobs[job_id]["zip_bytes"] = zip_bytes
    jobs[job_id]["done"] = True

def get_status(job_id):
    return jobs.get(job_id, None)
