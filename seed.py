import sys
import os
from sqlalchemy.orm import Session
from config.database import SessionLocal, engine, Base
from auth.models import Student
from study_plans.models import Program, Specialization, Course, Topic
from case_studies.models import CaseStudy
from auth.utils import get_password_hash

def seed_db():
    db = SessionLocal()
    
    # 1. Create a dummy student/admin
    from auth.models import Admin
    print("Seeding Admin and Student credentials...")
    
    # Create Admin: admin@admin.com / admin
    admin_pwd = get_password_hash("admin")
    admin_user = db.query(Admin).filter(Admin.email == "admin@admin.com").first()
    if not admin_user:
        admin_user = Admin(
            name="Super Admin",
            email="admin@admin.com",
            hash_pass=admin_pwd,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
    
    # Create Candidate (Student): user@admin.com / user
    student_pwd = get_password_hash("user")
    student_user = db.query(Student).filter(Student.email == "user@admin.com").first()
    if not student_user:
        student_user = Student(
            name="Test User",
            email="user@admin.com",
            phone="1234567890",
            hash_pass=student_pwd,
            is_active=True
        )
        db.add(student_user)
        db.commit()

    # 2. Create Programs
    print("Seeding Programs...")
    programs_data = ["MBA", "BBA", "PGPM"]
    for p_name in programs_data:
        p = db.query(Program).filter(Program.name == p_name).first()
        if not p:
            p = Program(name=p_name, is_active=True)
            db.add(p)
            db.commit()
            db.refresh(p)
            
            # Create Specializations for this program
            specs = [f"{p_name} Finance", f"{p_name} Marketing", f"{p_name} HR"]
            for s_name in specs:
                s = Specialization(name=s_name, program_id=p.id, is_active=True)
                db.add(s)
                db.commit()
                db.refresh(s)
                
                # Create Courses for this specialization
                courses = [
                    {"name": f"{s_name} 101", "code": f"C101-{s.id}"},
                    {"name": f"{s_name} Advanced", "code": f"C201-{s.id}"}
                ]
                for c_data in courses:
                    c = Course(name=c_data["name"], code=c_data["code"], specialization_id=s.id, is_active=True)
                    db.add(c)
                    db.commit()
                    db.refresh(c)
                    
                    # Create Topics
                    topics = [f"Topic 1 for {c.name}", f"Topic 2 for {c.name}"]
                    for t_name in topics:
                        t = Topic(name=t_name, course_id=c.id, is_active=True)
                        db.add(t)
                        db.commit()

    # 3. Create Case Studies
    print("Seeding Case Studies...")
    case_studies_data = [
        {
            "name": "Dr. Arijit Bhattacharya",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/KgViamGlhYI/hqdefault.jpg",
            "youtube_video_id": "KgViamGlhYI",
            "youtube_url": "https://youtu.be/KgViamGlhYI",
            "author": "ICFAI Business School",
            "display_order": 1,
            "is_active": True
        },
        {
            "name": "Dr. Dimple Pandey",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/nC8KEjvJ6Oc/hqdefault.jpg",
            "youtube_video_id": "nC8KEjvJ6Oc",
            "youtube_url": "https://www.youtube.com/watch?v=nC8KEjvJ6Oc",
            "author": "ICFAI Business School",
            "display_order": 2,
            "is_active": True
        },
        {
            "name": "Dr. Swaha Shome",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/T3W-1XHz5D4/hqdefault.jpg",
            "youtube_video_id": "T3W-1XHz5D4",
            "youtube_url": "https://www.youtube.com/watch?v=T3W-1XHz5D4",
            "author": "ICFAI Business School",
            "display_order": 3,
            "is_active": True
        },
        {
            "name": "Dr. Roopali Srivastava",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/qQcFEgQlSPY/hqdefault.jpg",
            "youtube_video_id": "qQcFEgQlSPY",
            "youtube_url": "https://youtu.be/qQcFEgQlSPY",
            "author": "ICFAI Business School",
            "display_order": 4,
            "is_active": True
        },
        {
            "name": "Dr Priyanka Dhingra",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/d5KoY78mNPk/hqdefault.jpg",
            "youtube_video_id": "d5KoY78mNPk",
            "youtube_url": "https://youtu.be/d5KoY78mNPk",
            "author": "ICFAI Business School",
            "display_order": 5,
            "is_active": True
        },
        {
            "name": "Prof Chitvan Mehrotra",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/nQ6B0QkUv-4/hqdefault.jpg",
            "youtube_video_id": "nQ6B0QkUv-4",
            "youtube_url": "https://youtu.be/nQ6B0QkUv-4",
            "author": "ICFAI Business School",
            "display_order": 6,
            "is_active": True
        },
        {
            "name": "Prof Kedar Dunakhe",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/_iaFe3heD_E/hqdefault.jpg",
            "youtube_video_id": "_iaFe3heD_E",
            "youtube_url": "https://youtu.be/_iaFe3heD_E",
            "author": "ICFAI Business School",
            "display_order": 7,
            "is_active": True
        },
        {
            "name": "Prof Nitin Bolinjkar",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/CqsBy_pK93g/hqdefault.jpg",
            "youtube_video_id": "CqsBy_pK93g",
            "youtube_url": "https://youtu.be/CqsBy_pK93g",
            "author": "ICFAI Business School",
            "display_order": 8,
            "is_active": True
        },
        {
            "name": "Prof Punit Neb",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/-0xzom5XZSo/hqdefault.jpg",
            "youtube_video_id": "-0xzom5XZSo",
            "youtube_url": "https://youtu.be/-0xzom5XZSo",
            "author": "ICFAI Business School",
            "display_order": 9,
            "is_active": True
        },
        {
            "name": "Prof Shobha Pillai",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/CGHRjGyiEBU/hqdefault.jpg",
            "youtube_video_id": "CGHRjGyiEBU",
            "youtube_url": "https://www.youtube.com/watch?v=CGHRjGyiEBU",
            "author": "ICFAI Business School",
            "display_order": 10,
            "is_active": True
        },
        {
            "name": "Dr. Vidhu K Mathur • Marketing",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/qMednEHhuNc/hqdefault.jpg",
            "youtube_video_id": "qMednEHhuNc",
            "youtube_url": "https://youtu.be/qMednEHhuNc",
            "author": "ICFAI Business School",
            "display_order": 11,
            "is_active": True
        },
        {
            "name": "Dr. Kapil Agrawal,Marketing",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/D1hBDUg73VA/hqdefault.jpg",
            "youtube_video_id": "D1hBDUg73VA",
            "youtube_url": "https://youtu.be/D1hBDUg73VA",
            "author": "ICFAI Business School",
            "display_order": 12,
            "is_active": True
        },
        {
            "name": "Dr. Shweta Jain • HR",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/9LenJCElUng/hqdefault.jpg",
            "youtube_video_id": "9LenJCElUng",
            "youtube_url": "https://youtu.be/9LenJCElUng",
            "author": "ICFAI Business School",
            "display_order": 13,
            "is_active": True
        },
        {
            "name": "Dr. Sumedha Soni • HR",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/jefRClwkcgc/hqdefault.jpg",
            "youtube_video_id": "jefRClwkcgc",
            "youtube_url": "https://youtu.be/jefRClwkcgc",
            "author": "ICFAI Business School",
            "display_order": 14,
            "is_active": True
        },
        {
            "name": "CA. Sukriti Khatri • Finance",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/QCmFbRObCQ0/hqdefault.jpg",
            "youtube_video_id": "QCmFbRObCQ0",
            "youtube_url": "https://youtu.be/QCmFbRObCQ0",
            "author": "ICFAI Business School",
            "display_order": 15,
            "is_active": True
        },
        {
            "name": "Dr. Archana Rathore • IT & Operations",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/fCIIWjWGz0A/hqdefault.jpg",
            "youtube_video_id": "fCIIWjWGz0A",
            "youtube_url": "https://youtu.be/fCIIWjWGz0A",
            "author": "ICFAI Business School",
            "display_order": 16,
            "is_active": True
        },
        {
            "name": "Dr. Amita Chourasiya • IT & Operations",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/SLhG895zGF0/hqdefault.jpg",
            "youtube_video_id": "SLhG895zGF0",
            "youtube_url": "https://youtu.be/SLhG895zGF0",
            "author": "ICFAI Business School",
            "display_order": 17,
            "is_active": True
        },
        {
            "name": "Dr. Vinay Khandewal • Finance",
            "subtitle": "IBS Jaipur",
            "thumbnail": "https://i.ytimg.com/vi/ZwNdarA4O0c/hqdefault.jpg",
            "youtube_video_id": "ZwNdarA4O0c",
            "youtube_url": "https://youtu.be/ZwNdarA4O0c",
            "author": "ICFAI Business School",
            "display_order": 18,
            "is_active": True
        },
        {
            "name": "Dr. Mohammad Shariq • Marketing",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/3I6OxjZ2F7M/hqdefault.jpg",
            "youtube_video_id": "3I6OxjZ2F7M",
            "youtube_url": "https://www.youtube.com/watch?v=3I6OxjZ2F7M",
            "author": "ICFAI Business School",
            "display_order": 19,
            "is_active": True
        },
        {
            "name": "Prof.Shweta Agrawal • IT",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/FTRfzXIUOJY/hqdefault.jpg",
            "youtube_video_id": "FTRfzXIUOJY",
            "youtube_url": "https://www.youtube.com/watch?v=FTRfzXIUOJY",
            "author": "ICFAI Business School",
            "display_order": 20,
            "is_active": True
        },
        {
            "name": "Prof.Sanjeev Sareen • Operations",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/1bQNigMLHbY/hqdefault.jpg",
            "youtube_video_id": "1bQNigMLHbY",
            "youtube_url": "https://www.youtube.com/watch?v=1bQNigMLHbY",
            "author": "ICFAI Business School",
            "display_order": 21,
            "is_active": True
        },
        {
            "name": "Prof. Vineeta Jha • Marketing",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/7NCJsXVE7YM/hqdefault.jpg",
            "youtube_video_id": "7NCJsXVE7YM",
            "youtube_url": "https://www.youtube.com/watch?v=7NCJsXVE7YM",
            "author": "ICFAI Business School",
            "display_order": 22,
            "is_active": True
        },
        {
            "name": "Prof Rajesh Mishra • Finance",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/F4yB6yy24Rs/hqdefault.jpg",
            "youtube_video_id": "F4yB6yy24Rs",
            "youtube_url": "https://www.youtube.com/watch?v=F4yB6yy24Rs",
            "author": "ICFAI Business School",
            "display_order": 23,
            "is_active": True
        },
        {
            "name": "Dr.Bhavna Chhabra • Finance",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/xw_XViF9hXQ/hqdefault.jpg",
            "youtube_video_id": "xw_XViF9hXQ",
            "youtube_url": "https://www.youtube.com/watch?v=xw_XViF9hXQ",
            "author": "ICFAI Business School",
            "display_order": 24,
            "is_active": True
        },
        {
            "name": "Prof Shweta Sharma • IT",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/CHcV_dgjYC0/hqdefault.jpg",
            "youtube_video_id": "CHcV_dgjYC0",
            "youtube_url": "https://www.youtube.com/watch?v=CHcV_dgjYC0",
            "author": "ICFAI Business School",
            "display_order": 25,
            "is_active": True
        },
        {
            "name": "Dr. Mona Sahay • HR",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/rFdy2UBVljo/hqdefault.jpg",
            "youtube_video_id": "rFdy2UBVljo",
            "youtube_url": "https://www.youtube.com/watch?v=rFdy2UBVljo",
            "author": "ICFAI Business School",
            "display_order": 26,
            "is_active": True
        },
        {
            "name": "Prof. Mohammad Shariq • Marketing",
            "subtitle": "IBS Gurgaon",
            "thumbnail": "https://i.ytimg.com/vi/i5T7VnsuyRQ/hqdefault.jpg",
            "youtube_video_id": "i5T7VnsuyRQ",
            "youtube_url": "https://www.youtube.com/watch?v=i5T7VnsuyRQ",
            "author": "ICFAI Business School",
            "display_order": 27,
            "is_active": True
        },
        {
            "name": "Dr. Davinder Suri",
            "subtitle": "IBS Mumbai",
            "thumbnail": "https://i.ytimg.com/vi/NjAwrD_yxs8/hqdefault.jpg",
            "youtube_video_id": "NjAwrD_yxs8",
            "youtube_url": "https://www.youtube.com/watch?v=NjAwrD_yxs8",
            "author": "ICFAI Business School",
            "display_order": 28,
            "is_active": True
        },
        {
            "name": "Dr Girish Kulkarni • Marketing",
            "subtitle": "IBS Pune",
            "thumbnail": "https://i.ytimg.com/vi/X1aOUP5SINQ/hqdefault.jpg",
            "youtube_video_id": "X1aOUP5SINQ",
            "youtube_url": "https://youtu.be/X1aOUP5SINQ",
            "author": "ICFAI Business School",
            "display_order": 29,
            "is_active": True
        },
        {
            "name": "Dr Irfan Inamdar • Marketing",
            "subtitle": "IBS Pune",
            "thumbnail": "https://i.ytimg.com/vi/mAmtQOZ8G4A/hqdefault.jpg",
            "youtube_video_id": "mAmtQOZ8G4A",
            "youtube_url": "https://youtu.be/mAmtQOZ8G4A",
            "author": "ICFAI Business School",
            "display_order": 30,
            "is_active": True
        },
        {
            "name": "Prof Sudhir Dravid • Finance",
            "subtitle": "IBS Pune",
            "thumbnail": "https://i.ytimg.com/vi/9EoGleF7r0Q/hqdefault.jpg",
            "youtube_video_id": "9EoGleF7r0Q",
            "youtube_url": "https://youtu.be/9EoGleF7r0Q",
            "author": "ICFAI Business School",
            "display_order": 31,
            "is_active": True
        },
        {
            "name": "Dr Saumya Misra • Finance",
            "subtitle": "IBS Pune",
            "thumbnail": "https://i.ytimg.com/vi/_gsJM92QudM/hqdefault.jpg",
            "youtube_video_id": "_gsJM92QudM",
            "youtube_url": "https://youtu.be/_gsJM92QudM",
            "author": "ICFAI Business School",
            "display_order": 32,
            "is_active": True
        },
        {
            "name": "Dr Jaysingh Bhosale • IT & Operations",
            "subtitle": "IBS Pune",
            "thumbnail": "https://i.ytimg.com/vi/07uk4Br9OTs/hqdefault.jpg",
            "youtube_video_id": "07uk4Br9OTs",
            "youtube_url": "https://youtu.be/07uk4Br9OTs",
            "author": "ICFAI Business School",
            "display_order": 33,
            "is_active": True
        },
        {
            "name": "Prof Moushmi Dasgupta • IT & Operations",
            "subtitle": "IBS Pune",
            "thumbnail": "https://i.ytimg.com/vi/-yDz2296ONg/hqdefault.jpg",
            "youtube_video_id": "-yDz2296ONg",
            "youtube_url": "https://youtu.be/-yDz2296ONg",
            "author": "ICFAI Business School",
            "display_order": 34,
            "is_active": True
        },
        {
            "name": "Dr Pallvi Vadehra • HR",
            "subtitle": "IBS Pune",
            "thumbnail": "https://i.ytimg.com/vi/yUWHTQplKfM/hqdefault.jpg",
            "youtube_video_id": "yUWHTQplKfM",
            "youtube_url": "https://youtu.be/yUWHTQplKfM",
            "author": "ICFAI Business School",
            "display_order": 35,
            "is_active": True
        }
    ]

    for cs_data in case_studies_data:
        existing_cs = db.query(CaseStudy).filter(CaseStudy.youtube_video_id == cs_data["youtube_video_id"]).first()
        if not existing_cs:
            cs = CaseStudy(**cs_data)
            db.add(cs)
            db.commit()

    print("Database seeded successfully!")
    db.close()

if __name__ == "__main__":
    seed_db()
