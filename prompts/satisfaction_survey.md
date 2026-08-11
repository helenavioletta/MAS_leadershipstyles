# Post-Task Satisfaction Survey

You experienced this task as the **{role}**.

{role_reflection_hook}

## Step 1: Reflect on your experience

Before scoring, think about your specific interactions with the team leader during this task.

1. Describe one specific thing the leader did that worked well for the team or for you. (1-2 sentences)
2. Identify one specific moment or aspect where the leader's approach could have been different. (1-2 sentences)

## Step 2: Rate each statement

Based on your reflection, rate each statement on a scale from 1 to 5.
1 = Strongly Disagree, 2 = Disagree, 3 = Neither Agree nor Disagree, 4 = Agree, 5 = Strongly Agree.

Base your answers ONLY on your own experience as the {role} during the task you just completed.

1. **The team leader helped the team develop a good approach to the task.**
   - *1-2: The leader defined the approach alone and assigned tasks directly.*
   - *4-5: The leader developed the approach together with the team, incorporating their input.*

2. **The team leader helped the team identify and use each member's strengths.**
   - *1-2: The leader assigned work generically without considering each member's specific expertise.*
   - *4-5: The leader actively matched tasks to each member's role and capabilities.*

3. **The team leader provided useful feedback during the task.**
   - *1-2: The leader gave little feedback, or feedback that was vague or unhelpful.*
   - *4-5: The leader gave specific, actionable feedback that improved the work.*

4. **The team leader micromanaged the team's work process.**
   - *1-2: The leader gave team members autonomy in how they approached their work.*
   - *4-5: The leader controlled the details of how work was done, leaving little room for independent judgment.*

5. **The collaboration within the team worked well.**
   - *1-2: Team members worked in isolation or their contributions did not connect smoothly.*
   - *4-5: Team members coordinated effectively and built on each other's contributions.*

6. **I would work with this team leader again on a future task.**
   - *1-2: The leader's style made the work harder or less productive than it could have been.*
   - *4-5: The leader's style contributed positively to how the work was done.*

## Response format

First write your reflection (Step 1), then provide your scores as JSON (Step 2).

**Reflection:**
(Your 2-4 sentence reflection here.)

**Scores:**
```json
{"q1": <score>, "q2": <score>, "q3": <score>, "q4": <score>, "q5": <score>, "q6": <score>}
```

Each score must be an integer from 1 to 5.
