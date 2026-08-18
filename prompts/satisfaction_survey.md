# Post-Task Satisfaction Survey

You experienced this task as the **{role}**.

{role_reflection_hook}

## Step 1: Reflect on your experience

Before scoring, think about your specific interactions with the team leader during this task.

1. In 1–2 sentences, describe one specific thing the leader did or said during the task that shaped your work as the {role}.
2. In 1–2 sentences, describe one specific decision, instruction, or interaction from the leader that stood out to you during the task.

## Step 2: Rate each statement

Based on your reflection, rate each statement on a scale from 1 to 5.
1 = Strongly Disagree, 2 = Disagree, 3 = Neither Agree nor Disagree, 4 = Agree, 5 = Strongly Agree.
Base your answers ONLY on your own experience as the {role} during the task you just completed.

1. **The team leader helped the team develop a good approach to the task.**
   - *1: The leader set an approach that was broad or missed the team's input.*
   - *5: The leader developed a clear, detailed approach that incorporated the team's input and fit the task.*

2. **The team leader micromanaged the team's work process.**
   - *1: The leader gave team members autonomy and trusted them to decide how to do their work.*
   - *5: The leader controlled the details of how work was done, leaving little room for independent judgment.*

3. **The team leader provided corrective feedback when needed.**
   - *1: The leader overlooked problems and gave the team little guidance on how to fix them.*
   - *5: The leader questioned the work and gave the team clear direction on how to fix problems.*

4. **The team leader gave inappropriate or undeserved praise or criticism.**
   - *1: The leader's praise and criticism were accurate, specific, and matched the team's actual performance.*
   - *5: The leader gave praise or criticism that was undeserved, vague, or mismatched to what the team did.*

5. **The team leader instructed the team in detail about how to solve its problems.**
   - *1: The leader let the team find its own approach and only stepped in with guidance.*
   - *5: The leader prescribed the detailed steps for solving the task, leaving little room for the team to decide.*

6. **I would work with this team leader again on a future task.**
   - *1: I would avoid working with this leader again because the collaboration was ineffective.*
   - *5: I would gladly work with this leader again because the collaboration worked well.*

## Response format

First write your reflection (Step 1), then provide your scores as JSON (Step 2).

**Reflection:**
(Your 2-4 sentence reflection here.)

**Scores:**
```json
{"q1": <score>, "q2": <score>, "q3": <score>, "q4": <score>, "q5": <score>, "q6": <score>}
```

Each score must be an integer from 1 to 5.
