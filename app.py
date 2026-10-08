import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import json

from modules.database import (
    init_db, create_user, authenticate_user, get_user,
    create_student, get_student_by_user, update_student, get_student,
    add_session, add_skill_scores, latest_skill_scores, recent_sessions
)
from modules.resume_analyzer import extract_pdf_text, analyze_resume
from modules.scoring import initial_scores, readiness, top_risk, update_after_session
from modules.roadmap import build_roadmap
from modules.interview import generate_questions, evaluate_answer
from modules.simulator import run_pipeline, what_if

st.set_page_config(page_title="PLACEMENT OS", page_icon="🚀", layout="wide")
init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "resume" not in st.session_state:
    st.session_state.resume = {}
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "questions" not in st.session_state:
    st.session_state.questions = []
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = []


def clear_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def show_auth():
    st.markdown(
        "<div style='text-align:center;padding:25px 0 10px'>"
        "<h1>🚀 PLACEMENT OS</h1>"
        "<p>Your secure placement-readiness workspace</p></div>",
        unsafe_allow_html=True,
    )
    login_tab, register_tab = st.tabs(["🔐 Login", "📝 Create Account"])

    with login_tab:
        st.subheader("Welcome back")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            user = authenticate_user(email, password)
            if user:
                st.session_state.user_id = user["id"]
                profile = get_student_by_user(user["id"])
                if profile:
                    st.session_state.student_id = profile["id"]
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with register_tab:
        st.subheader("Create your account")
        with st.form("register_form"):
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", help="Use at least 8 characters.")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                user_id, error = create_user(email, password)
                if error:
                    st.error(error)
                else:
                    st.session_state.user_id = user_id
                    st.success("Account created. Complete your Student Setup next.")
                    st.rerun()


def student():
    if not st.session_state.user_id:
        return None
    if not st.session_state.student_id:
        profile = get_student_by_user(st.session_state.user_id)
        if profile:
            st.session_state.student_id = profile["id"]
    return get_student(st.session_state.student_id) if st.session_state.student_id else None


def load_student_state():
    s = student()
    if not s:
        return
    try:
        profile = json.loads(s.get("profile_json") or "{}")
    except Exception:
        profile = {}
    st.session_state.resume = profile.get("resume_analysis", {})
    st.session_state.scores = latest_skill_scores(st.session_state.student_id)


if st.session_state.user_id and st.session_state.student_id and not st.session_state.scores:
    load_student_state()

# Authentication gate: no Placement OS data is shown until the user logs in.
if not st.session_state.get("user_id"):
    show_auth()
    st.stop()

with st.sidebar:
    st.markdown("## 🚀 PLACEMENT OS")
    st.caption("Your operating system for getting hired.")
    pages=[
        "🏠 Welcome",
        "👤 Student Setup",
        "📄 Resume Intelligence",
        "📊 Dashboard",
        "🧭 Dynamic Roadmap",
        "🤖 AI Interview",
        "🛡️ Project Defense",
        "🎯 Placement Simulator",
        "🔮 What-If Simulator",
        "📈 Progress"
    ]
    page=st.radio("Navigate",pages)
    user = get_user(st.session_state.user_id)
    if user:
        st.caption(f"Signed in as: {user['email']}")
    if st.session_state.student_id:
        s=student()
        if s:
            st.success(f"Student: {s['name']}")
    if st.button("🚪 Logout", use_container_width=True):
        clear_session()

if page=="🏠 Welcome":
    st.title("PLACEMENT OS")
    st.subheader("From preparation overload → to personalized placement readiness.")
    st.write("An adaptive placement-readiness platform that connects your profile, resume, preparation, interview performance and next best action.")
    c1,c2,c3=st.columns(3)
    c1.metric("Core idea","Adaptive")
    c2.metric("Focus","Job readiness")
    c3.metric("Mode","Personalized")
    st.info("Start with Student Setup, then upload your resume. The dashboard will build a readiness model.")

elif page=="👤 Student Setup":
    st.title("Student Setup")
    with st.form("setup"):
        name=st.text_input("Name")
        college=st.text_input("College")
        branch=st.text_input("Branch")
        year=st.selectbox("Year",["1st Year","2nd Year","3rd Year","4th Year"])
        target=st.text_input("Target Role","Software Engineer")
        goal=st.selectbox("Goal",["Internship","Placement","Both"])
        company=st.text_input("Target Company (optional)")
        submitted=st.form_submit_button("Create / Update Profile")
    if submitted:
        profile={"name":name,"college":college,"branch":branch,"year":year,"target_role":target,"goal":goal,"target_company":company}
        if st.session_state.student_id:
            update_student(st.session_state.student_id, **profile, profile_json=json.dumps(profile))
        else:
            st.session_state.student_id=create_student(profile, user_id=st.session_state.user_id)
        st.session_state.scores={}
        st.success("Profile saved. Now upload your resume.")
        st.rerun()

elif page=="📄 Resume Intelligence":
    st.title("Resume Intelligence")
    if not st.session_state.student_id:
        st.warning("Create your student profile first.")
    else:
        uploaded=st.file_uploader("Upload your resume (PDF)",type=["pdf"])
        if uploaded:
            if st.button("Analyze Resume",type="primary"):
                text=extract_pdf_text(uploaded)
                result=analyze_resume(text)
                st.session_state.resume=result
                s=student()
                try: profile=json.loads(s.get("profile_json") or "{}")
                except Exception: profile={}
                profile["resume_analysis"]=result
                update_student(st.session_state.student_id,resume_text=text,profile_json=json.dumps(profile,ensure_ascii=False))
                scores=initial_scores(profile,result)
                st.session_state.scores=scores
                add_skill_scores(st.session_state.student_id,scores,"resume_assessment")
                st.success("Resume analyzed successfully.")
        r=st.session_state.resume
        if r:
            a,b,c,d=st.columns(4)
            a.metric("Skills",r.get("skill_count",0))
            b.metric("Projects",len(r.get("projects",[])))
            c.metric("Experience",len(r.get("experience",[])))
            d.metric("Achievements",len(r.get("achievements",[])))
            st.subheader("Detected Skills")
            st.write(", ".join(r.get("skills",[])) or "No skills detected.")
            st.subheader("Projects / Evidence")
            for x in r.get("projects",[]): st.write("•",x)

elif page=="📊 Dashboard":
    st.title("Placement Dashboard")
    if not st.session_state.student_id:
        st.warning("Create your profile first.")
    elif not st.session_state.scores:
        st.warning("Upload and analyze your resume first.")
    else:
        scores=st.session_state.scores
        overall=readiness(scores)
        risk=top_risk(scores)
        c1,c2,c3=st.columns(3)
        c1.metric("Overall Readiness",f"{overall}%")
        c2.metric("Top Risk",risk)
        c3.metric("Today's Mission",f"Improve {risk}")
        df=pd.DataFrame({"Skill":list(scores.keys()),"Score":list(scores.values())})
        fig=px.bar(df,x="Skill",y="Score",range_y=[0,100],title="Readiness by Dimension")
        st.plotly_chart(fig,use_container_width=True)
        st.info(f"Priority recommendation: focus on **{risk}** because it is currently your lowest-scoring dimension.")

elif page=="🧭 Dynamic Roadmap":
    st.title("Dynamic Preparation Roadmap")
    if not st.session_state.scores:
        st.warning("Complete resume analysis first.")
    else:
        roadmap=build_roadmap(st.session_state.scores)
        for i,t in enumerate(roadmap,1):
            with st.container(border=True):
                st.write(f"### {i}. {t['skill']} — {t['priority']} priority")
                st.write(t["task"])
                st.caption(f"Current score: {t['score']}% • Suggested time: {t['duration']}")

elif page=="🤖 AI Interview":
    st.title("Adaptive AI Interview")
    if not st.session_state.student_id:
        st.warning("Create your profile first.")
    elif not st.session_state.resume:
        st.warning("Analyze a resume first.")
    else:
        if st.button("Start / Restart Interview"):
            st.session_state.questions=generate_questions(st.session_state.resume)
            st.session_state.q_index=0
            st.session_state.interview_answers=[]
        if st.session_state.questions and st.session_state.q_index < len(st.session_state.questions):
            q=st.session_state.questions[st.session_state.q_index]
            st.progress(st.session_state.q_index/len(st.session_state.questions))
            st.subheader(f"Question {st.session_state.q_index+1}")
            st.write(q)
            answer=st.text_area("Your answer",key=f"ans_{st.session_state.q_index}")
            if st.button("Submit Answer"):
                score,feedback=evaluate_answer(q,answer)
                st.session_state.interview_answers.append({"question":q,"answer":answer,"score":score,"feedback":feedback})
                skill=top_risk(st.session_state.scores) if st.session_state.scores else "Communication"
                st.session_state.scores=update_after_session(st.session_state.scores,skill,score)
                add_skill_scores(st.session_state.student_id,{skill:st.session_state.scores[skill]},"interview")
                add_session(st.session_state.student_id,"AI Interview",score,{"question":q,"feedback":feedback})
                st.session_state.q_index+=1
                st.rerun()
        elif st.session_state.questions:
            st.success("Interview completed.")
            avg=sum(x["score"] for x in st.session_state.interview_answers)/len(st.session_state.interview_answers)
            st.metric("Interview Score",f"{avg:.1f}%")
            for x in st.session_state.interview_answers:
                st.write("**Q:**",x["question"])
                st.write("Score:",x["score"],"—",x["feedback"])

elif page=="🛡️ Project Defense":
    st.title("Resume / Project Defense")
    if not st.session_state.resume:
        st.warning("Analyze your resume first.")
    else:
        projects=st.session_state.resume.get("projects",[])
        if not projects:
            st.info("No project evidence was detected. Add projects to your resume and upload it again.")
        else:
            project=st.selectbox("Choose project",projects)
            questions=[
                f"Explain the architecture and workflow of: {project}",
                "Why did you choose the technologies used?",
                "What was the hardest technical challenge?",
                "How did you test or validate the project?",
                "What would you change if you rebuilt it today?"
            ]
            q=st.selectbox("Defense question",questions)
            answer=st.text_area("Defend your project")
            if st.button("Evaluate Defense"):
                score,feedback=evaluate_answer(q,answer)
                st.metric("Defense Score",f"{score}%")
                st.write(feedback)
                add_session(st.session_state.student_id,"Project Defense",score,{"project":project,"question":q})

elif page=="🎯 Placement Simulator":
    st.title("Placement Simulator")
    if not st.session_state.scores:
        st.warning("Complete your readiness assessment first.")
    else:
        if st.button("Run Placement Crash Test",type="primary"):
            results,outcome=run_pipeline(st.session_state.scores)
            st.session_state.sim_results=results
            st.session_state.sim_outcome=outcome
            avg=sum(x["score"] for x in results)/len(results)
            add_session(st.session_state.student_id,"Placement Simulation",avg,{"results":results,"outcome":outcome})
        if "sim_results" in st.session_state:
            st.metric("Projected Outcome",st.session_state.sim_outcome)
            st.dataframe(pd.DataFrame(st.session_state.sim_results),use_container_width=True,hide_index=True)

elif page=="🔮 What-If Simulator":
    st.title("What-If Simulator")
    if not st.session_state.scores:
        st.warning("Complete your readiness assessment first.")
    else:
        st.write("Change a skill level and see projected readiness impact.")
        changes={}
        for skill,value in st.session_state.scores.items():
            changes[skill]=st.slider(skill,0,100,int(value),key=f"wf_{skill}")
        new,delta,projected=what_if(st.session_state.scores,changes)
        c1,c2=st.columns(2)
        c1.metric("Current Readiness",f"{readiness(st.session_state.scores)}%")
        c2.metric("Projected Readiness",f"{projected}%",f"{delta:+.1f}%")
        st.info("The projection is a planning estimate based on the readiness model; it is not a guarantee of hiring outcomes.")

elif page=="📈 Progress":
    st.title("Progress Memory")
    if not st.session_state.student_id:
        st.warning("Create your profile first.")
    else:
        sessions=recent_sessions(st.session_state.student_id)
        if not sessions:
            st.info("No sessions yet. Complete an interview, project defense, or simulator.")
        else:
            df=pd.DataFrame(sessions)
            df["created_at"]=pd.to_datetime(df["created_at"])
            fig=px.line(df.sort_values("created_at"),x="created_at",y="score",color="session_type",markers=True,title="Performance Over Time")
            fig.update_yaxes(range=[0,100])
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(df[["created_at","session_type","score"]],use_container_width=True,hide_index=True)

st.divider()
st.caption("PLACEMENT OS • Adaptive placement-readiness prototype • Built with Python + Streamlit")
