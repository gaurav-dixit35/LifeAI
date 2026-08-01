from __future__ import annotations


def urgency_label(risk_level: int) -> str:
    if risk_level >= 85:
        return "critical"
    if risk_level >= 70:
        return "high"
    if risk_level >= 45:
        return "elevated"
    if risk_level >= 20:
        return "guarded"
    return "low"


def recommendation_for(risk_level: int) -> str:
    if risk_level >= 85:
        return "urgent_support"
    if risk_level >= 60:
        return "support"
    if risk_level >= 35:
        return "caution"
    return "steady"


def detect_needs(lowered: str, topic: str, situation_details: list[str], risk_level: int) -> list[str]:
    needs: list[str] = ["clarity"]
    if risk_level >= 60:
        needs.append("emotional stabilization")
    if topic in {"stress", "relationship"}:
        needs.append("emotional safety")
    if topic in {"career", "money", "general", "study", "productivity"}:
        needs.append("decision structure")
    if topic in {"health", "tech", "home", "schedule", "food"}:
        needs.append("practical fix")
    if "fight" in situation_details or "trust" in situation_details:
        needs.append("communication repair")
    if "debt" in situation_details or "rent" in situation_details:
        needs.append("practical stability")
    if "can't sleep" in situation_details or "burnout" in situation_details or "routine reset" in situation_details:
        needs.append("recovery")
    if any(phrase in lowered for phrase in ["alone", "lonely", "no one", "isolated"]):
        needs.append("human support")

    deduped: list[str] = []
    for need in needs:
        if need not in deduped:
            deduped.append(need)
    return deduped[:4]


def build_response_strategy(topic: str, detected_needs: list[str], urgency: str) -> str:
    if urgency in {"high", "critical"}:
        return "Prioritize emotional safety, slower decision-making, and real human support before complex analysis."
    if topic == "health":
        return "Give a short practical response first, suggest a simple relief step, and escalate only if symptoms sound stronger or persistent."
    if topic == "tech":
        return "Start with the most likely troubleshooting step, then give one clean fallback."
    if topic == "home":
        return "Focus on the safest quick fix now and a proper repair later if needed."
    if topic == "schedule":
        return "Help the user recover control quickly and reduce the damage from delay."
    if topic == "study":
        return "Reduce overwhelm, break the work into a realistic study block, and protect consistency over perfection."
    if topic == "productivity":
        return "Shrink the problem into one workable routine adjustment and remove the biggest distraction first."
    if topic == "food":
        return "Keep the advice realistic, routine-friendly, and based on repeatable food choices rather than ideal plans."
    if topic == "relationship":
        return "Validate the emotional impact, reduce reactivity, then move toward one clear conversation or boundary."
    if topic == "career":
        return "Reduce confusion by turning the situation into criteria, options, and one lower-risk experiment."
    if topic == "money":
        return "Stabilize the practical pressure first, then rebuild clarity from urgent constraints and real numbers."
    if topic == "stress":
        return "Lower mental and physical overload first, then solve only the most important issue from a calmer state."
    if "communication repair" in detected_needs:
        return "Use a calm, repair-focused approach that protects honesty without escalating conflict."
    return "Combine emotional grounding with a practical next-step plan tailored to the user's situation."


def build_decision_lens(topic: str, situation_details: list[str], risk_level: int) -> str:
    if risk_level >= 85:
        return "The right lens is safety first. The priority is not optimization or perfect judgment. It is slowing everything down and bringing in real human support."
    if topic == "health":
        return "Judge this by symptom strength, trigger, and whether a simple reset step is enough or proper care is needed."
    if topic == "tech":
        return "Judge this by the fastest reliable fix, not by trying many random things."
    if topic == "home":
        return "Judge this by safety first, then quick containment, then proper repair."
    if topic == "schedule":
        return "Judge this by how to save the next important part of the day first."
    if topic == "study":
        return "Judge the plan by whether it is realistic enough to repeat, not by whether it looks perfect on paper."
    if topic == "productivity":
        return "Judge the next move by whether it reduces friction and makes action easier within the next hour."
    if topic == "food":
        return "Judge the choice by whether it is balanced, available, and easy enough to keep doing for a week."
    if topic == "career":
        if "switch job" in situation_details or "leave job" in situation_details:
            return "Judge this by four realities: financial runway, emotional cost, growth potential, and whether staying is teaching you anything worth the strain."
        if "interview" in situation_details:
            return "Judge this by preparedness, not by worth. The goal is to show fit and evidence, not to prove your value as a person."
        return "Judge career options by stability, direction, energy cost, and future learning rather than by momentary fear."
    if topic == "relationship":
        if "fight" in situation_details:
            return "Judge the next step by whether it increases honesty, safety, and the chance of repair, not by whether it helps you win the argument."
        if "trust" in situation_details:
            return "Judge this by evidence and consistency. Hope matters, but trust should be rebuilt through repeated behavior, not promises alone."
        return "Judge the next move by clarity, boundaries, and whether the relationship can support a truthful conversation."
    if topic == "money":
        return "Judge every option by what stabilizes the next few weeks first, then what prevents the same pressure from repeating."
    if topic == "stress":
        return "Judge the situation by what is actually urgent versus what only feels urgent because your system is overloaded."
    if "decision" in situation_details:
        return "Judge the options by reversibility, information gained, and emotional cost instead of forcing one perfect answer immediately."
    return "Judge the next move by whether it creates more clarity, more stability, and less emotional distortion."


def build_follow_up_question(topic: str, situation_details: list[str], detected_needs: list[str], lowered: str) -> str:
    if topic == "health":
        return "How strong is it right now, and did anything specific trigger it?"
    if topic == "tech":
        return "What exactly is failing, and what have you already tried once?"
    if topic == "home":
        return "Do you need a quick temporary fix right now or a proper repair plan?"
    if topic == "schedule":
        return "What is the most urgent thing this delay could affect right now?"
    if topic == "study":
        return "What is making studying hardest right now: focus, planning, energy, or pressure?"
    if topic == "productivity":
        return "What is the main thing pulling you off track right now: distraction, low energy, or too many priorities?"
    if topic == "food":
        return "What part of eating well is hardest right now: planning, cravings, timing, or budget?"
    if topic == "career":
        if "switch job" in situation_details or "leave job" in situation_details:
            return "What is pushing you harder right now: burnout, lack of growth, bad environment, or financial fear about leaving?"
        if "interview" in situation_details:
            return "What part of the interview feels hardest right now: preparation, confidence, or fear of rejection?"
        return "Which career option feels most important to you right now, and what is making it hard to choose?"
    if topic == "relationship":
        if "fight" in situation_details:
            return "What happened in the fight, and what do you most want from the next conversation: repair, clarity, apology, or distance?"
        if "trust" in situation_details:
            return "What would need to change before trust could feel real again?"
        return "What do you most need from this relationship situation right now: understanding, repair, a boundary, or a decision?"
    if topic == "money":
        if "debt" in situation_details:
            return "What is the most urgent financial pressure at this moment: debt payments, cash flow, or fear about what happens next?"
        if "rent" in situation_details:
            return "How close is the rent deadline, and what money or support options are realistically available right now?"
        return "Which financial pressure is hurting you most right now: monthly survival, debt, or uncertainty about income?"
    if topic == "stress":
        if "can't sleep" in situation_details:
            return "How long has your sleep been affected, and what seems to trigger the worst nights?"
        if "burnout" in situation_details:
            return "What is draining you most right now: workload, people pressure, emotional exhaustion, or lack of rest?"
        return "What is the single biggest source of stress right now?"
    if "human support" in detected_needs:
        return "Who in real life feels even slightly safe to talk to if this gets heavier?"
    if any(phrase in lowered for phrase in ["should i", "what should i do", "choice", "decision"]):
        return "If you had to name the top two options, what are they?"
    return "What part of this situation feels most painful or confusing right now?"


def build_suggestions(lowered: str, personality_mode: str, topic: str, situation_details: list[str]) -> list[str]:
    suggestions = [
        "Pause long enough to separate facts from fears.",
        "Choose one next step that reduces uncertainty today.",
        "Notice whether you need support, rest, or a concrete plan first.",
    ]
    if topic == "health":
        return [
            "Start with the simplest likely cause before assuming the worst.",
            "Reduce the trigger, rest a bit, and hydrate if that fits the symptom.",
            "If it worsens, repeats, or feels unusual, get proper medical help.",
        ]
    if topic == "tech":
        return [
            "Try one clean troubleshooting step at a time.",
            "Check power, connection, restart, or storage before deeper fixes.",
            "Protect important data or work with a backup option if needed.",
        ]
    if topic == "home":
        return [
            "Handle the immediate inconvenience or mess first.",
            "Use a safe temporary workaround if it helps today.",
            "Plan a proper repair if the issue can repeat or cause damage.",
        ]
    if topic == "schedule":
        return [
            "Recover the next important step first.",
            "Send one quick update if someone is waiting on you.",
            "Fix the weak point so the same slip does not repeat tomorrow.",
        ]
    if topic == "study":
        return [
            "Shrink the study target to one session you can actually finish.",
            "Choose the highest-weight topic instead of trying to cover everything evenly.",
            "Use short revision rounds and a real break so your brain keeps absorbing.",
        ]
    if topic == "productivity":
        return [
            "Choose one priority before opening distracting apps or tabs.",
            "Lower the friction around the first task so starting feels easier.",
            "Protect a short focus block before trying to fix your whole routine.",
        ]
    if topic == "food":
        return [
            "Make the next meal balanced and simple instead of chasing a perfect diet reset.",
            "Plan around what you can realistically buy, cook, and repeat this week.",
            "Use consistency, hydration, and timing before extreme restrictions.",
        ]
    if topic == "career":
        if "switch job" in situation_details or "leave job" in situation_details:
            suggestions[1] = "Compare staying versus switching using stability, growth, skill-building, and emotional cost."
        elif "interview" in situation_details:
            suggestions[1] = "Prepare your story around strengths, proof, and direction instead of trying to sound perfect."
        else:
            suggestions[1] = "List your top career options and compare them by energy, growth, and stability."
    if topic == "relationship":
        if "fight" in situation_details:
            suggestions[1] = "Write the calm version of the conversation before you speak again."
        elif "trust" in situation_details:
            suggestions[1] = "Focus on what evidence you need before deciding whether trust can be rebuilt."
        else:
            suggestions[1] = "Write the conversation you wish you could have before you send any message."
    if topic == "money":
        if "debt" in situation_details:
            suggestions[1] = "Split the problem into urgent debt pressure, monthly survival, and one stabilizing action this week."
        elif "rent" in situation_details:
            suggestions[1] = "Treat housing pressure as the first constraint and build the rest of the plan around it."
        else:
            suggestions[1] = "Reduce the problem to numbers first so the emotional load feels smaller."
    if topic == "stress":
        if "can't sleep" in situation_details:
            suggestions[1] = "Protect sleep and physical recovery first because exhausted thinking will distort every choice."
        elif "burnout" in situation_details:
            suggestions[1] = "Stop measuring yourself by output for a moment and diagnose what is actually draining you."
        else:
            suggestions[1] = "Lower your nervous system first, then decide what actually deserves your energy."
    if topic == "general" and "decision" in situation_details:
        suggestions[1] = "Turn the decision into two or three concrete options so your mind stops fighting fog."
    if personality_mode == "friend":
        suggestions[0] = "Take one deep breath and stop treating this moment like you must fix your whole life tonight."
    if personality_mode == "mentor":
        suggestions[2] = "Look for the pattern beneath the event so you improve the next decision, not just this one."
    return suggestions


def build_action_plan(topic: str, situation_details: list[str]) -> list[str]:
    plan = [
        "Write a two-line summary of the situation in plain language so your mind stops carrying it vaguely.",
        "Identify the one decision, conversation, or boundary that matters most in the next 24 hours.",
        "Choose one low-risk move that creates clarity instead of more pressure.",
        "Check what changed emotionally after acting, then decide the next step from that calmer state.",
    ]
    if topic == "health":
        return [
            "Notice the symptom, its intensity, and likely trigger.",
            "Take the safest simple relief step now.",
            "Watch whether it settles, worsens, or starts bringing stronger signs.",
        ]
    if topic == "tech":
        return [
            "Name the exact issue clearly.",
            "Try the most likely fix first: restart, reconnect, recharge, or free space.",
            "Use a backup option if the issue blocks urgent work.",
        ]
    if topic == "home":
        return [
            "Contain the inconvenience or mess first.",
            "Use the quickest safe workaround for today.",
            "Arrange a proper repair or replacement if it keeps affecting daily life.",
        ]
    if topic == "schedule":
        return [
            "Reduce the immediate delay first.",
            "Send one quick update if needed.",
            "Fix the trigger so the rest of the day gets cleaner.",
        ]
    if topic == "study":
        return [
            "List the exact topics or tasks still pending.",
            "Choose the most important block for today's session.",
            "Finish one focused round before deciding whether you need another.",
        ]
    if topic == "productivity":
        return [
            "Choose one task that matters more than the rest.",
            "Remove the biggest distraction for the next focused block.",
            "Review what pulled your attention away and fix that friction point next.",
        ]
    if topic == "food":
        return [
            "Plan the next two meals using what is realistic for your day.",
            "Add one balanced option with protein, water, and a real eating time.",
            "Notice what triggers bad eating decisions and reduce that trigger tomorrow.",
        ]
    if topic == "stress":
        plan[0] = "Take five slow breaths, unclench your body, and lower your physical stress before analyzing the situation."
        if "can't sleep" in situation_details:
            plan[2] = "Reduce today's expectations and protect recovery so lack of sleep does not drive the next decision."
        else:
            plan[2] = "Reduce today's expectations to one meaningful win and one recovery action."
    if topic == "career":
        if "switch job" in situation_details or "leave job" in situation_details:
            plan[2] = "Write the staying plan and the leaving plan side by side, then compare risk, energy, and runway."
        elif "interview" in situation_details:
            plan[2] = "Prepare three strong examples that show competence, growth, and why this role fits your direction."
        else:
            plan[2] = "Compare your best options using values, income stability, energy, and learning potential."
    if topic == "relationship":
        if "fight" in situation_details:
            plan[2] = "Draft a calm message that names the issue, owns your part, and asks for one honest conversation."
        elif "trust" in situation_details:
            plan[2] = "List what would need to be true for trust to feel real again before making any big emotional decision."
        else:
            plan[2] = "Draft a calm message that describes the issue without blame and asks for one honest conversation."
    if topic == "money":
        if "debt" in situation_details:
            plan[2] = "List debt pressure, minimum obligations, and one action that buys you more time or stability this week."
        elif "rent" in situation_details:
            plan[2] = "Map rent deadline, available cash, and the fastest action that reduces housing risk immediately."
        else:
            plan[2] = "List the real numbers, immediate constraints, and one action that improves stability this week."
    if topic == "general" and "decision" in situation_details:
        plan[2] = "Write the top two options and one low-risk experiment that gives you more information."
    return plan


def build_immediate_actions(topic: str, situation_details: list[str], risk_level: int) -> list[str]:
    actions = [
        "Name the real problem in one sentence so you stop reacting to a vague cloud.",
        "Do one grounding action before making the next decision.",
    ]
    if topic == "health":
        if "headache" in situation_details:
            return [
                "Rest your eyes and step away from the screen for a while.",
                "Drink water and avoid pushing through if the pain is building.",
                "If the headache feels severe, unusual, or keeps coming back, get proper medical advice.",
            ]
        if "fever" in situation_details:
            return [
                "Rest, hydrate, and check your temperature properly.",
                "Avoid overexerting yourself for today.",
                "Get medical help if fever is high, persistent, or comes with stronger symptoms.",
            ]
        return [
            "Reduce the likely trigger first.",
            "Take the simplest safe relief step now.",
            "Watch whether the symptom is easing or getting worse.",
        ]
    if topic == "tech":
        if "internet issue" in situation_details:
            return [
                "Restart Wi-Fi, data, or the router once if you can.",
                "Check whether the issue is only one device or the whole network.",
                "Use a backup connection if urgent work is blocked.",
            ]
        return [
            "Restart or reconnect the device once cleanly.",
            "Check charge, storage, or connection before deeper fixes.",
            "Switch to a backup method if urgent work is blocked.",
        ]
    if topic == "home":
        return [
            "Handle the immediate mess, leak, or inconvenience first.",
            "Use a safe temporary workaround for today.",
            "Plan a proper fix if the problem can repeat or cause damage.",
        ]
    if topic == "schedule":
        return [
            "Recover the next important step instead of panicking about the whole day.",
            "Send a quick update if someone is waiting on you.",
            "Fix the one thing that caused the slip, like alarm, timing, or transport backup.",
        ]
    if topic == "study":
        return [
            "Choose the exact chapter, topic, or task for the next study block.",
            "Set a short timer and start before optimizing the whole plan.",
            "Remove one distraction so the block has a real chance to work.",
        ]
    if topic == "productivity":
        return [
            "Pick one task and make it visible in front of you.",
            "Close or move the thing that usually derails you first.",
            "Work for one short focused block before deciding whether motivation is present.",
        ]
    if topic == "food":
        return [
            "Decide the next real meal or snack instead of grazing reactively.",
            "Drink water and avoid making the next food choice while very depleted.",
            "Use the easiest healthier option already available to you right now.",
        ]
    if risk_level >= 70:
        actions[0] = "Pause major decisions for the moment and lower the emotional temperature first."
        actions.append("Tell one trusted person that this situation feels heavy instead of carrying it alone.")
    if topic == "career":
        actions[1] = "List the top two career options and the main fear inside each one."
    if topic == "relationship":
        actions[1] = "Write what hurt, what you need, and what outcome you want before speaking again."
    if topic == "money":
        actions[1] = "Open the numbers, deadlines, and obligations so the pressure becomes concrete."
    if topic == "stress":
        actions[1] = "Reduce stimulation, unclench your body, and create a calmer state before judging the situation."
    return actions[:3]


def build_short_term_actions(topic: str, situation_details: list[str]) -> list[str]:
    if topic == "health":
        return [
            "Reduce the main trigger for the rest of the day.",
            "Track whether the symptom improves, repeats, or gets stronger.",
            "Escalate to proper care if it does not settle as expected.",
        ]
    if topic == "tech":
        return [
            "Back up important work once the issue is stable.",
            "Repair or update only after the urgent task is protected.",
            "Keep one fallback for essential work tools.",
        ]
    if topic == "home":
        return [
            "Replace or repair the item if it affects daily function.",
            "Clear the area so the problem does not spread or repeat immediately.",
            "Keep one simple backup for common home inconveniences.",
        ]
    if topic == "schedule":
        return [
            "Protect the rest of the day with one cleaner plan.",
            "Set a backup alarm, reminder, or travel margin.",
            "Prevent one repeat failure instead of over-correcting everything at once.",
        ]
    if topic == "study":
        return [
            "Build the next few study blocks around priority topics, not guilt.",
            "Review what method worked best for focus and repeat that pattern.",
            "Keep the plan short enough that you can return tomorrow without dread.",
        ]
    if topic == "productivity":
        return [
            "Reduce the repeat distraction that keeps stealing time.",
            "Protect one consistent focus window in your day.",
            "Use a visible plan for the next few tasks instead of relying on memory.",
        ]
    if topic == "food":
        return [
            "Plan tomorrow's meals loosely so stress does not choose for you.",
            "Stock one or two easy, better options that fit your routine.",
            "Notice whether sleep, money, or stress is driving the food problem more than appetite is.",
        ]
    if topic == "career":
        return [
            "Compare your top options using stability, growth, energy, and self-respect.",
            "Run one low-risk test such as applying, networking, or skill-building instead of making the whole decision in your head.",
            "Notice whether the current path is merely hard or actually corrosive.",
        ]
    if topic == "relationship":
        return [
            "Have one calmer, more focused conversation instead of repeating the whole conflict.",
            "Use clear statements about impact, responsibility, and what needs to change next.",
            "Watch whether the other person moves toward repair or only toward defensiveness.",
        ]
    if topic == "money":
        return [
            "Separate immediate obligations from longer-term money problems.",
            "Negotiate, delay, or restructure the most urgent pressure where possible.",
            "Choose one stabilizing move that lowers next week's risk, not just today's panic.",
        ]
    if topic == "stress":
        return [
            "Reduce active problems to one priority and one recovery action per day.",
            "Protect sleep, food, and breaks so your body is not trying to think while depleted.",
            "Delay major life conclusions until your system is less overloaded.",
        ]
    return [
        "Turn the problem into concrete options instead of emotional fog.",
        "Choose one conversation, boundary, or experiment that gives you new information.",
        "Review what changed after that step before deciding the rest.",
    ]


def build_long_term_actions(topic: str) -> list[str]:
    if topic == "health":
        return [
            "Notice recurring triggers and patterns.",
            "Build a better routine for rest, posture, hydration, or timely care if this repeats.",
        ]
    if topic == "tech":
        return [
            "Keep backups, updates, and spare accessories in better shape.",
            "Build one reliable fallback for essential devices and internet access.",
        ]
    if topic == "home":
        return [
            "Keep basic home essentials or repair contacts ready for repeat issues.",
            "Reduce the chance of the same inconvenience through simple maintenance.",
        ]
    if topic == "schedule":
        return [
            "Create more buffer around your most time-sensitive routines.",
            "Use reminders and backups so one miss does not derail the day.",
        ]
    if topic == "study":
        return [
            "Build a repeatable study rhythm instead of relying on deadline panic.",
            "Track which methods help you retain information with less stress.",
        ]
    if topic == "productivity":
        return [
            "Design your day around fewer, clearer priorities.",
            "Create an environment that makes focus easier by default.",
        ]
    if topic == "food":
        return [
            "Build a simple eating structure you can repeat on busy days too.",
            "Use routine and preparation to make better choices easier over time.",
        ]
    if topic == "career":
        return [
            "Build a career direction based on values and sustainability, not only on escaping discomfort.",
            "Strengthen skills or relationships that increase future options.",
        ]
    if topic == "relationship":
        return [
            "Build a relationship standard around honesty, emotional safety, and repair capacity.",
            "Notice recurring conflict patterns so you stop solving only the latest episode.",
        ]
    if topic == "money":
        return [
            "Create a financial recovery plan that includes stability, buffer, and repetition prevention.",
            "Strengthen the habit of checking money in clear numbers before stress turns it into fear.",
        ]
    if topic == "stress":
        return [
            "Rebuild life around sustainable energy, not emergency pacing.",
            "Identify the recurring inputs that push you into overload and reduce them earlier next time.",
        ]
    return [
        "Use this situation to build a clearer decision process for future problems.",
        "Track what actually helps you regain clarity under pressure.",
    ]


def build_avoid_now(topic: str, risk_level: int) -> list[str]:
    avoid = [
        "Do not confuse strong emotion with final truth.",
        "Do not try to solve the whole future in one sitting.",
    ]
    if topic == "health":
        return [
            "Do not ignore worsening or unusual symptoms.",
            "Do not keep pushing through if your body clearly needs rest.",
        ]
    if topic == "tech":
        return [
            "Do not try random fixes without checking the likely cause first.",
            "Do not risk important data if a backup is possible.",
        ]
    if topic == "home":
        return [
            "Do not ignore safety or damage risk just because the problem seems ordinary.",
            "Do not trust a weak temporary fix for too long.",
        ]
    if topic == "schedule":
        return [
            "Do not waste time blaming yourself while the next urgent step still needs handling.",
            "Do not let one delay ruin the whole day mentally.",
        ]
    if risk_level >= 70:
        avoid.append("Do not make high-stakes choices while heavily activated or isolated.")
    if topic == "relationship":
        avoid.append("Do not send emotionally loaded messages just to discharge the pressure.")
    if topic == "money":
        avoid.append("Do not make relief-seeking financial moves without checking the real numbers first.")
    if topic == "career":
        avoid.append("Do not treat fear of regret as proof that staying or leaving is right.")
    if topic == "stress":
        avoid.append("Do not use exhaustion as evidence that your whole life is failing.")
    return avoid[:4]


def build_when_to_seek_support(topic: str, risk_level: int, situation_details: list[str]) -> list[str]:
    guidance = [
        "Bring in trusted support if the situation keeps getting heavier instead of clearer.",
    ]
    if topic == "health":
        return [
            "Get proper medical help if symptoms become severe, unusual, or do not improve.",
        ]
    if topic == "tech":
        return [
            "Get technical help if the issue risks data loss or still blocks important work after basic fixes.",
        ]
    if topic == "home":
        return [
            "Get outside help if the issue affects safety, water, electricity, or repeated daily use.",
        ]
    if topic == "schedule":
        return [
            "Ask for help or send a clear update if the delay affects something important and you cannot recover it alone.",
        ]
    if topic == "relationship":
        guidance.append("Get outside support if every conversation turns into the same injury without repair.")
    if topic == "money":
        guidance.append("Ask for practical support early if basic stability like rent, food, or debt deadlines are at risk.")
    if topic == "stress" or "can't sleep" in situation_details:
        guidance.append("Seek more support if sleep, appetite, or daily functioning keeps dropping.")
    if risk_level >= 60:
        guidance.insert(0, "Bring in real human support now if you feel unsafe, unable to regulate, or close to making a harmful decision.")
    return guidance[:3]


def build_safety_notes(risk_level: int) -> list[str]:
    if risk_level >= 85:
        return [
            "If you may be in immediate danger or thinking about harming yourself, contact local emergency services or a crisis helpline right now.",
            "Move this from self-coaching to real human support as soon as possible.",
        ]
    if risk_level >= 60:
        return [
            "Do not make major decisions while highly activated. Pause and involve someone you trust.",
            "If the situation becomes unsafe, seek immediate human support.",
        ]
    return [
        "Slow decisions down if emotions spike while you are acting.",
    ]


def infer_strengths(lowered: str) -> list[str]:
    strengths = [
        "You are actively looking for clarity instead of impulsively reacting.",
        "You have enough self-awareness to notice that the situation is affecting you.",
    ]
    if "help" in lowered or "advice" in lowered:
        strengths.append("You are willing to ask for support before the situation hardens.")
    if any(word in lowered for word in ["career", "job", "future", "study"]):
        strengths.append("You care about making a thoughtful long-term decision, not just a fast one.")
    if any(word in lowered for word in ["friend", "relationship", "family"]):
        strengths.append("You still value the relationship enough to reflect before acting.")
    return strengths[:3]


def build_hidden_risks(lowered: str, risk_level: int) -> list[str]:
    risks = [
        "Overthinking may create the illusion of progress while keeping action delayed.",
        "Strong emotion can make temporary discomfort feel like a permanent truth.",
    ]
    if any(word in lowered for word in ["career", "job", "work", "study"]):
        risks.append("Fear of choosing wrong may keep you stuck between options instead of learning from one real step.")
    if any(word in lowered for word in ["friend", "relationship", "partner", "family"]):
        risks.append("Responding while activated could turn a solvable issue into a deeper rupture.")
    if any(word in lowered for word in ["money", "finance", "debt"]):
        risks.append("Stress may push you toward short-term relief instead of stable decision-making.")
    if risk_level >= 60:
        risks.append("Isolation will amplify the pressure if you try to carry this alone.")
    return risks[:4]


def build_personalized_guidance_note(user_profile: dict[str, object], topic: str) -> str:
    support_style = str(user_profile.get("preferred_support_style", "balanced guidance"))
    strengths = list(user_profile.get("strengths", []))
    stressors = list(user_profile.get("stressors", []))
    themes = list(user_profile.get("themes", []))

    note = f"I am leaning toward {support_style} because that seems to fit how you process support."
    if topic in themes:
        note += f" This topic also appears to be part of a recurring personal pattern around {topic}."
    elif themes:
        note += f" A nearby recurring theme is {themes[0]}, which may be shaping how this problem feels."
    if strengths:
        note += f" One useful strength to lean on is that you are {strengths[0]}."
    if stressors:
        note += f" A pressure amplifier in your history is {stressors[0]}."
    return note
