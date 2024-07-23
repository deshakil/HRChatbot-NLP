

from flask import Flask, request, jsonify
from pymongo import MongoClient
import uuid
from datetime import datetime, timezone

app = Flask(__name__)

# Connecting to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['shakilco']
job_openings = db['JobOpenings']
organizational_policy=db['OrganizationalPolicy']
job_applications=db['JobApplications']

@app.route('/')
def home():
    return "Hello, HTTPS!"

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    action = req.get('queryResult').get('action')
    
    if action == 'showJobOpenings':
        return show_job_openings()
    elif action == 'specificJobDetails':
        return specific_job_details(req)
    elif action == 'selectionProcess':
        return selection_process(req)
    elif action == 'generalHRQuestions':
        return general_hr_questions(req)
    elif action == 'JobDetails':
        return queries_job_detailed(req)
    elif action == 'OrgBased' :
        return queries_organizational_policy(req)
    elif action == 'Apply4Job' :
        return apply_for_job()
    else:
        return {}
    
def apply_for_job():
    req = request.get_json(silent=True, force=True)
    job_role = req['queryResult']['parameters'].get('jobroles')
    applicant_name = req['queryResult']['parameters'].get('name')
    applicant_email = req['queryResult']['parameters'].get('email')
    resume_link = req['queryResult']['parameters'].get('resumelink')

    
    application_id = str(uuid.uuid4())


    application_data = {
        'application_id': application_id,
        'job_role': job_role,
        'applicant_name': applicant_name,
        'applicant_email': applicant_email,
        'resume_link': resume_link,
        'application_date': datetime.now(timezone.utc)
    }
    job_applications.insert_one(application_data)

    response = {
        "fulfillmentText": f"Your application for {job_role} has been submitted with application ID: {application_id}, we will get back to you soon...",
        "source": "webhookdata"
    }
    return jsonify(response)
  
    

def queries_organizational_policy(req):
    policy_section = req['queryResult']['parameters'].get('organizationalbased')
    policy_data = organizational_policy.find_one({}, {"_id": 0, f"organizational_policy.{policy_section}": 1})

    if policy_data and 'organizational_policy' in policy_data and policy_section in policy_data['organizational_policy']:
        section_policies = policy_data['organizational_policy'][policy_section]
        response_list = [f"{policy['policy']}: {policy['description']}" for policy in section_policies]
        response = "\n".join(response_list)
    else:
        response = f"Sorry, I couldn't find the {policy_section} section."

    return make_response(response)



def queries_job_detailed(req):
    query = req['queryResult']['parameters'].get('jobdes')
    job_role = req['queryResult']['parameters'].get('jobroles')
    job = job_openings.find_one(
        {"$or": [{"job_id": job_role}, {"title": job_role}]},
        {"_id": 0}
    )

    if job:
        if query == 'preparation_resources':
            response = f"Preparation Resources: {', '.join(job.get('preparation_resources', []))}\n"
        elif query == 'selection_process':
            response = f"Selection Process: {', '.join(job.get('selection_process', []))}\n"
        else:
            response = "Sorry, I couldn't understand your request. Please try again."
    else:
        response = "Sorry, I couldn't find details for that job role."

    return make_response(response)

def show_job_openings():
    jobs = job_openings.find({}, {"_id": 0, "job_id": 1, "title": 1, "location": 1})
    job_list = [f"Job ID: {job['job_id'].zfill(3)} - {job['title']} in {job['location']}" for job in jobs]
    response = "These are the current openings we have:\n\n" + "\n\n".join(job_list)
    return make_response(response)

def specific_job_details(req):
    """job_id = req['queryResult']['parameters'].get('JobRole')
    job = job_openings.find_one({"job_id": job_id}, {"_id": 0})
    job1=job_openings.fin_one({"title":job_id},{"_id":0})
    if job or job1:
        response = f"Job Title: {job['title']}\nLocation: {job['location']}\nResponsibilities: {', '.join(job['responsibilities'])}\nSkills: {job['skills']}\nExperience: {job['experience']}"
    else:
        response = "Sorry, I couldn't find details for that job ID."
    return make_response(response)"""
    job_role_or_id = req['queryResult']['parameters'].get('jobroles')
    print(f"Received JobRoles parameter: {job_role_or_id}")
    job = job_openings.find_one(
        {"$or": [{"job_id": job_role_or_id}, {"title": job_role_or_id}]},
        {"_id": 0}
    )
    
    print(f"Found job: {job}") 
    if job:
        response = (f"Job Title: {job['title']}\n"
                    f"Location: {job['location']}\n"
                    f"Responsibilities: {', '.join(job['responsibilities'])}\n"
                    f"Skills: {job['skills']}\n"
                    f"Experience: {job['experience']}")
    else:
        response = "Sorry! currently we are not having that role in our rganization, please check again later :-( "
    return make_response(response)

def selection_process(req):
    job_role_or_id = req['queryResult']['parameters'].get('JobRoles')
    job = job_openings.find_one(
        {"$or": [{"job_id": job_role_or_id}, {"title": job_role_or_id}]},
        {"_id": 0}
    )
    if job:
        response = "The selection process includes: " + ", ".join(job['selection_process'])
    else:
        response = "Sorry, I couldn't find the selection process for that job ID."
    return make_response(response)


def make_response(text):
    return jsonify({
        "fulfillmentText": text,
        "source": "webhookdata"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)





