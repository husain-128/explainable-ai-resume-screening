from flask import Flask, request, render_template, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
from pypdf import PdfReader  # For PDF text extraction
import string  # For text normalization

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages; change in production
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload size
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Predefined list of common skills (expandable for more realism)
SKILLS_LIST = [
    'python', 'java', 'javascript', 'machine learning', 'data analysis',
    'sql', 'html', 'css', 'react', 'flask', 'tensorflow', 'pandas',
    'numpy', 'git', 'docker', 'aws', 'linux', 'c++', 'r', 'excel',
    'mongodb', 'php', 'mysql', 'node.js', 'angular', 'vue', 'django',
    'spring', 'kubernetes', 'azure', 'gcp', 'postgresql', 'oracle',
    'c#', 'ruby', 'rails', 'scala', 'hadoop', 'spark', 'tableau',
    'power bi', 'sas', 'matlab', 'swift', 'kotlin', 'flutter', 'ionic',
    'firebase', 'heroku', 'jenkins', 'ansible', 'terraform', 'graphql',
    'rest api', 'soap', 'xml', 'json', 'linux', 'windows', 'macos',
    'bash', 'powershell', 'vim', 'emacs', 'intellij', 'vscode', 'eclipse'
]

# Ensure uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def normalize_text(text):
    """Normalize text: lowercase, remove punctuation, strip extra whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return ' '.join(text.split())  # Remove extra spaces

def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyPDF2. Returns text or None if error."""
    try:
        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        # Gracefully handle unreadable PDFs
        return None

def get_skills_in_text(text, skills_list):
    """Find skills in normalized text using substring match."""
    normalized_text = normalize_text(text)
    return [skill for skill in skills_list if skill in normalized_text]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form data
        file = request.files.get('resume')
        job_desc = request.form.get('job_desc', '').strip()
        
        # Validation
        if not file or file.filename == '':
            flash('Please upload a resume PDF.', 'error')
            return redirect(url_for('index'))
        if not job_desc:
            flash('Please enter a job description.', 'error')
            return redirect(url_for('index'))
        if not file.filename.lower().endswith('.pdf'):
            flash('Only PDF files are allowed.', 'error')
            return redirect(url_for('index'))
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)
        if resume_text is None:
            flash('Unable to read the PDF. Please ensure it is a text-based PDF.', 'error')
            os.remove(file_path)  # Clean up
            return redirect(url_for('index'))
        
        # Get skills from resume and job desc
        resume_skills = get_skills_in_text(resume_text, SKILLS_LIST)
        job_skills = get_skills_in_text(job_desc, SKILLS_LIST)
        
        # Calculate matched and missing skills
        matched_skills = list(set(resume_skills) & set(job_skills))
        missing_skills = list(set(job_skills) - set(matched_skills))
        
        # Calculate match percentage
        if job_skills:
            match_percentage = round((len(matched_skills) / len(job_skills)) * 100, 2)
        else:
            match_percentage = 0.0
        
        # Explanation
        explanation = (
            f"The match score is calculated by identifying skills from the job description "
            f"that are also present in the resume (using keyword matching). "
            f"There are {len(job_skills)} skills in the job description. "
            f"{len(matched_skills)} of them match the resume, resulting in a {match_percentage}% match. "
            f"Missing skills are those in the job description but not found in the resume."
        )
        
        # Clean up uploaded file
        os.remove(file_path)
        
        # Render results
        return render_template('results.html', 
                               match_percentage=match_percentage,
                               matched_skills=matched_skills,
                               missing_skills=missing_skills,
                               explanation=explanation)
    
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # No debug by default