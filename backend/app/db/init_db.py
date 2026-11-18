"""Database table initialization, achievement badge catalog, and sports-science coaching knowledge base."""

from sqlalchemy.orm import Session

from app.db.database import Base, engine
from app.db.models import Achievement, CoachingKnowledge

DEFAULT_ACHIEVEMENTS = [
    {
        "code": "FIRST_PREDICTION",
        "name": "Data-Driven Debut",
        "description": "Completed your first live AI calorie burn prediction using the trained model.",
        "icon": "sparkles",
        "points": 50,
        "category": "ai",
    },
    {
        "code": "FIVE_PREDICTIONS",
        "name": "Analytics Regular",
        "description": "Logged 5 or more AI workout predictions.",
        "icon": "bar-chart",
        "points": 120,
        "category": "ai",
    },
    {
        "code": "FIRST_SESSION",
        "name": "Session Starter",
        "description": "Logged your first real training performance record.",
        "icon": "flame",
        "points": 50,
        "category": "training",
    },
    {
        "code": "CONSISTENCY_3",
        "name": "Momentum Builder",
        "description": "Logged 3 or more training sessions.",
        "icon": "calendar-check",
        "points": 150,
        "category": "consistency",
    },
    {
        "code": "ENDURANCE_1000",
        "name": "Kilocalorie Crusher",
        "description": "Accumulated 1,000+ total calories across logged training sessions.",
        "icon": "zap",
        "points": 200,
        "category": "milestone",
    },
    {
        "code": "VIDEO_BREAKDOWN",
        "name": "Film Room Analyst",
        "description": "Uploaded and analyzed a training video using OpenCV movement tracking.",
        "icon": "video",
        "points": 100,
        "category": "video",
    },
    {
        "code": "PLAN_COMPLETED",
        "name": "Plan Executor",
        "description": "Completed at least 3 scheduled sessions in a personalized training program.",
        "icon": "award",
        "points": 175,
        "category": "training",
    },
    {
        "code": "CHALLENGE_FINISHER",
        "name": "Challenge Conqueror",
        "description": "Completed a training motivation challenge.",
        "icon": "trophy",
        "points": 250,
        "category": "challenge",
    },
]

# Curated, evidence-based sports coaching & exercise science knowledge base for training the Semantic Coaching AI
DEFAULT_COACHING_KNOWLEDGE = [
    # Endurance & Running
    ("endurance", "Running", "How do I improve my 5K or 10K running endurance and speed?",
     "Follow an 80/20 polarized structure: keep ~80% of weekly mileage in conversational Zone 2 (65-75% max HR) to build mitochondrial density and capillary networks, and dedicate 20% to one lactate-threshold tempo run (20-30 min comfortably hard) plus one VO2max interval session (e.g., 5x1000m with 2-3 min jog recovery). Cap weekly volume increases at <=10%.",
     "running,5k,10k,endurance,vo2max,zone2,tempo,aerobic"),
    ("endurance", "Running", "What is the optimal running cadence and stride technique?",
     "Most efficient distance runners maintain a cadence near 170-185 steps per minute with foot strike directly underneath the center of mass (avoiding overstriding with a locked knee). Keep tall posture with a slight forward lean from the ankles, relaxed shoulders, and 90-degree elbow drive.",
     "cadence,stride,biomechanics,running form,overstriding"),
    ("endurance", "Cycling", "How should I structure cycling endurance and FTP workouts?",
     "Build Functional Threshold Power (FTP) with 2x20 min sweet-spot intervals (88-93% FTP) twice weekly, paired with long Zone 2 endurance rides (90-150 min at 85-95 RPM cadence). Include one high-cadence neuromuscular spin drill session and one full recovery day.",
     "cycling,ftp,cadence,threshold,sweet spot,bike"),
    ("endurance", "Swimming", "How can swimmers improve stroke efficiency and lap endurance?",
     "Focus on high-elbow catch (early vertical forearm), horizontal body alignment with head neutral looking down, and bilateral breathing to balance shoulder load. Use pull-buoy + paddle sets for catch strength and 10x100m threshold repeats on 15-20s rest.",
     "swimming,stroke,freestyle,catch,lap,endurance"),
    ("endurance", "Rowing", "What is proper rowing technique and split pacing?",
     "Execute the drive in strict sequence: Legs -> Hips/Back -> Arms, and reverse cleanly on the recovery: Arms -> Hips -> Legs. Maintain a 1:2 drive-to-recovery ratio at 18-22 strokes/min for aerobic steady state and 26-30 spm for 2K race pace pieces.",
     "rowing,erg,drive,stroke rate,pacing,cardio"),
    ("endurance", "General", "How do heart rate training zones work?",
     "Estimate Max HR (~220 - age, or lab-tested). Zone 1 (50-60%): active recovery. Zone 2 (60-70%): aerobic base & fat oxidation. Zone 3 (70-80%): aerobic tempo. Zone 4 (80-90%): lactate threshold. Zone 5 (90-100%): VO2max and anaerobic sprint power.",
     "heart rate,bpm,zones,aerobic,anaerobic,threshold"),

    # Strength & Conditioning / Power
    ("strength", "Weight Training", "How do I build muscle mass and maximal strength effectively?",
     "For hypertrophy, accumulate 10-20 hard working sets per muscle group per week in the 6-12 rep range at RPE 7-9 (1-3 reps in reserve). For maximal strength, prioritize compound lifts (squat, hinge, press, pull) at 80-90% 1RM for 3-5 sets of 3-5 reps with 2.5-4 min rest.",
     "hypertrophy,muscle gain,strength,lifting,sets,reps,progressive overload"),
    ("strength", "General", "How do I increase explosive sprint speed and vertical jump power?",
     "Pair heavy lower-body strength (trap bar deadlift, back squat at 80-85% 1RM) with low-volume plyometrics (box jumps, broad jumps, pogo hops, 3x4-6 reps with full 2-3 min rest) and short 10-30m maximal acceleration sprints when completely fresh.",
     "speed,sprint,explosive,power,plyometrics,vertical jump,acceleration"),
    ("strength", "HIIT", "How often should athletes perform HIIT workouts per week?",
     "Limit true maximal HIIT sessions (85-95% max HR, e.g., 30s work / 30s rest or 4x4 min Norwegian intervals) to 2-3 non-consecutive days per week. Stacking HIIT daily elevates cortisol, spikes ACWR, and degrades power output.",
     "hiit,intervals,conditioning,tabata,anaerobic,frequency"),
    ("strength", "Football", "What strength and agility drills are best for football or soccer players?",
     "Combine eccentric hamstring strength (Nordic curls, RDLs), single-leg stability (Bulgarian split squats), repeated-sprint ability (6x40m shuttles on 25s rest), and reactive change-of-direction (5-10-5 pro-agility and mirror deceleration drills).",
     "football,soccer,agility,change of direction,sprint,hamstring"),
    ("strength", "Basketball", "How should basketball players train agility, lateral quickness, and jump durability?",
     "Prioritize lateral shuffle deceleration, defensive slide intervals, landing mechanics (soft knee-over-toe absorption), calf/Achilles isometric holds, and core anti-rotation strength to protect knees and ankles during high-frequency jumping.",
     "basketball,vertical,lateral,agility,landing,jump"),

    # Injury Prevention & Biomechanics
    ("injury_prevention", "General", "What is ACWR (Acute to Chronic Workload Ratio) and why does it matter?",
     "ACWR compares your 7-day acute training load to your 28-day chronic weekly average. An ACWR between 0.8 and 1.3 is the sweet spot for steady adaptation; values above 1.5 indicate a rapid workload spike associated with elevated overuse injury risk. Always consult a sports clinician for pain.",
     "acwr,workload,spike,overuse,injury risk,load management"),
    ("injury_prevention", "Running", "How can runners prevent shin splints, runner's knee, and Achilles tendinopathy?",
     "Avoid sudden weekly mileage spikes, strengthen hip abductors/glute medius (clamshells, monster walks, single-leg bridges), perform heavy slow calf raises (bent-knee & straight-knee), rotate cushioned footwear, and back off intensity immediately if localized bone/tendon pain worsens during warm-up.",
     "shin splints,knee pain,achilles,tendon,running injury,prevention"),
    ("injury_prevention", "General", "How should I structure a proper dynamic warm-up before training or matches?",
     "Use the RAMP protocol (10-12 min): Raise pulse (3 min light jog/jump rope), Activate & Mobilize (leg swings, world's greatest stretch, glute bridges, scapular wall slides), and Potentiate (3 progressive build-up strides or light sport-specific movement reps).",
     "warmup,warm-up,ramp,mobility,activation,injury prevention"),
    ("injury_prevention", "Weight Training", "How do I prevent lower back and shoulder injuries during weight training?",
     "Brace your core 360 degrees (Valsalva/diaphragmatic bracing) before every hinge or squat, maintain neutral spine alignment, balance pushing volume with equal horizontal/vertical pulling (face pulls, rows), and warm up rotator cuffs with external rotations.",
     "back pain,shoulder,rotator cuff,bracing,form,lifting safety"),
    ("injury_prevention", "General", "What are early warning signs of overtraining syndrome?",
     "Watch for elevated morning resting heart rate (+5-7 BPM above baseline), persistent heavy legs, declining workout output at the same RPE, fragmented sleep, irritability, or recurring minor illnesses. Respond with a 4-7 day deload (40-50% volume reduction).",
     "overtraining,deload,fatigue,resting heart rate,burnout,exhaustion"),

    # Recovery, Sleep & Nutrition
    ("recovery", "General", "How much sleep do athletes need for optimal recovery and performance?",
     "Competitive and recreational athletes training 4+ days/week perform best on 7.5 to 9 hours of consistent sleep per night. Deep slow-wave sleep drives growth hormone release and muscle repair; <6.5 hours impairs reaction time, glycogen resynthesis, and increases injury risk.",
     "sleep,recovery,rest,hormone,reaction time,fatigue"),
    ("recovery", "General", "What are daily hydration and electrolyte guidelines for athletes?",
     "Target ~35-45 mL of water per kg of body weight daily (typically 2.5-3.8 L/day), plus 400-800 mL per hour of intense sweat-heavy training. For sessions over 60 minutes or in hot climates, include 500-800 mg sodium/L to prevent cramping and cardiovascular drift.",
     "hydration,water,electrolytes,sodium,cramp,sweat"),
    ("recovery", "General", "What should I eat before and after intense workouts?",
     "Pre-workout (1.5-3 hrs prior): easily digested complex carbohydrates (1-2 g/kg) + moderate lean protein, low fat/fiber. Post-workout (within 1-2 hrs): 0.3-0.4 g/kg high-quality protein (25-40g) for muscle protein synthesis plus 0.8-1.2 g/kg carbohydrates to replenish muscle glycogen.",
     "nutrition,protein,carbs,pre-workout,post-workout,glycogen,fuel"),
    ("recovery", "General", "How should I manage calorie deficit for safe athletic weight loss without losing muscle?",
     "Use a modest 300-500 kcal daily deficit relative to Total Daily Energy Expenditure (guided by your trained calorie burn predictions), keep protein high (1.8-2.2 g/kg body weight), maintain 2-3 weekly resistance sessions, and fuel key high-intensity workouts with targeted carbs.",
     "weight loss,fat loss,calories,deficit,protein,lean mass"),
    ("recovery", "Yoga", "How do yoga and mobility sessions accelerate athletic recovery?",
     "Restorative yoga and static stretching (30-60s holds post-session) activate the parasympathetic nervous system, reduce resting heart rate, restore hip flexor/thoracic/ankle range of motion, and alleviate delayed onset muscle soreness without adding structural fatigue.",
     "yoga,mobility,flexibility,stretching,cooldown,soreness"),

    # Game Strategy & Tactics
    ("strategy", "General", "How do I analyze an opponent and build an effective counter-strategy?",
     "Audit three measurable dimensions: opponent pace/tempo, offensive vs defensive asymmetry, and late-game endurance drop-off. Against fast high-press opponents, compact spacing and counter into vacated transition lanes; against defensive low-block teams, increase tempo width and exploit set-piece efficiency.",
     "opponent,tactics,counter-strategy,matchup,scouting,game plan"),
    ("strategy", "General", "How do I peak and taper before a major competition or tournament?",
     "Implement a 7-14 day exponential taper before competition: cut total training volume by 40-50% while maintaining 80-90% of race/match intensity in short sharp bouts. This sheds accumulated fatigue while preserving neuromuscular sharpness and VO2max.",
     "taper,peak performance,competition,race day,tournament,periodization"),
    ("strategy", "General", "How does periodization work across a sports season?",
     "Divide your season into Macrocycles (full season), Mesocycles (3-6 week focused blocks: General Prep -> Specific Prep -> Peak/Competition -> Active Transition), and Microcycles (7-day weekly schedules alternating heavy, moderate, and recovery days).",
     "periodization,macrocycle,mesocycle,microcycle,season planning"),

    # Video Analysis & Skill Scoring
    ("video_biomechanics", "General", "How should I record training videos for accurate OpenCV movement analysis?",
     "Mount the camera on a stationary tripod perpendicular to the primary direction of movement, ensure good lighting and high subject-to-background contrast, capture full body height with margin, and keep clips 10-60 seconds focused on a single drill or rally.",
     "video,camera,recording,opencv,tracking,biomechanics,analysis"),
    ("video_biomechanics", "General", "How should I interpret OpenCV motion intensity and active movement ratio?",
     "Mean and peak motion intensity measure optical-flow pixel velocity across sampled frames, highlighting explosive bursts and tempo shifts. Active movement ratio reflects work-to-rest density within the clip, while centroid trajectory maps lateral vs vertical displacement symmetry.",
     "motion intensity,optical flow,trajectory,keyframes,video feedback"),
    ("mental_performance", "General", "How can athletes stay consistent and mentally focused under pressure?",
     "Use process-based micro-goals (execution cues like posture, breathing rhythm, and split targets) rather than outcome anxiety. Pair 4-4-6 box breathing pre-competition with pre-performance visualization and consistent gamified habit streaks.",
     "mental,focus,mindset,confidence,pressure,consistency,motivation"),
    ("mental_performance", "General", "How do athletes bounce back mentally after a tough loss or poor performance?",
     "Run a 24-hour objective debrief: separate measurable execution errors (e.g., pacing, sleep deficit, warm-up) from self-worth, write two actionable adjustments for the next practice, and immediately refocus on the next controllable training session.",
     "loss,setback,resilience,psychology,debrief,comeback"),
    ("ai_model", "General", "How does the ApexPulse trained calorie prediction model work?",
     "ApexPulse integrates your existing 300-tree ExtraTreesRegressor trained on 70,000 workout records (91.81% test R², 61.36 kcal MAE). Its top drivers are Duration (49.4%), Body Weight (19.1%), Heart Rate (9.3%), and Exercise Type. Every prediction includes an 80% ensemble interval and live what-if sensitivity comparisons.",
     "model,extra trees,calories,accuracy,r2,mae,ai prediction,confidence"),
    ("ai_model", "General", "How does continuous learning work in the ApexPulse Coaching AI?",
     "While preserving your original D:\\V3 ExtraTrees model read-only, ApexPulse trains a companion HistGradientBoosting Strain & Readiness Classifier (97%+ accuracy) and TF-IDF + LinearSVC Semantic Coaching NLP model directly on the 70,000-row dataset, your logged database sessions, and custom coaching knowledge entries whenever you click Retrain AI.",
     "continuous learning,retrain,strain classifier,nlp,database ai,machine learning"),
]


def init_db(db: Session | None = None) -> None:
    """Create all tables if they don't exist and seed badge & coaching knowledge catalogs."""
    Base.metadata.create_all(bind=engine)
    own_session = db is None
    if own_session:
        from app.db.database import SessionLocal

        db = SessionLocal()
    try:
        for item in DEFAULT_ACHIEVEMENTS:
            existing = db.query(Achievement).filter(Achievement.code == item["code"]).first()
            if not existing:
                db.add(Achievement(**item))

        existing_qs = {row[0] for row in db.query(CoachingKnowledge.question_pattern).all()}
        for cat, sport, q, ans, tags in DEFAULT_COACHING_KNOWLEDGE:
            if q not in existing_qs:
                db.add(
                    CoachingKnowledge(
                        category=cat,
                        sport=sport,
                        question_pattern=q,
                        answer=ans,
                        tags=tags,
                    )
                )
        db.commit()
    finally:
        if own_session:
            db.close()
