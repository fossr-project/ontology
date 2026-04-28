# OWLUnit Test Case Documentation for the BDI Ontology

This document explains the OWLUnit individuals used to validate the competency questions of the BDI Ontology against the toy dataset available at `https://w3id.org/fossr/ontology/bdi-tests`.

Each test individual is an instance of `owlunit:CompetencyQuestionVerification` and contains:

- a competency question;
- an input dataset;
- a SPARQL unit test;
- an expected SPARQL JSON result;
- the ontology under test: `https://w3id.org/fossr/ontology/bdi/`.

The tests validate whether the ontology and the example dataset can answer the competency questions that define the functional requirements of the BDI Ontology.

---

## Test Case 1  `unit-test-1`

**Competency question:** What are mental entities?

**Purpose:**  
This test verifies that all individuals classified as instances of `bdi:MentalEntity` or of one of its subclasses can be retrieved. It checks the ontologyâs ability to recognise beliefs, desires, intentions, and mental processes as mental entities.

**Query logic:**  
The query selects every individual `?entity` with a type `?type` such that `?type` is `bdi:MentalEntity` or a subclass of it, using the property path:

```sparql
?type rdfs:subClassOf* bdi:MentalEntity
```

**Expected result:**  
The expected output includes beliefs such as `Belief_Employment`, `Belief_ExamFailed`, `Belief_GoodAtScience`, `Belief_LogicalSkills`, and `Belief_LovesPC`; mental processes such as `BP_FailureRevision`, `DP_ResitDesire`, `IP_ResitIntention`, and `Planning_Graduate`; the desire `Desire_Graduate`; and intentions such as `Intention_Graduation`, `Intention_PassExams`, `Intention_ResitAlgorithms`, and `Intention_WriteThesis`.

**Validation focus:**  
The test validates the taxonomic organisation of the ontology under `bdi:MentalEntity`.

---

## Test Case 2  `unit-test-2`

**Competency question:** What mental states does an agent hold?

**Purpose:**  
This test checks which mental states are associated with the agent `ex:Mark`.

**Query logic:**  
The query retrieves all resources linked to `ex:Mark` through `bdi:hasMentalState` and returns their RDF type.

```sparql
ex:Mark bdi:hasMentalState ?state .
?state a ?type .
```

**Expected result:**  
The expected output contains Markâs beliefs, desire, and intentions, including:

- `Belief_Employment`
- `Belief_ExamFailed`
- `Belief_GoodAtScience`
- `Belief_LogicalSkills`
- `Belief_LovesPC`
- `Desire_Graduate`
- `Intention_Graduation`
- `Intention_PassExams`
- `Intention_ResitAlgorithms`
- `Intention_WriteThesis`

**Validation focus:**  
The test validates the relation between an agent and the mental states it holds.

---

## Test Case 3  `unit-test-3`

**Competency question:** What are the constituent mental entities that form part of a given mental entity?

**Purpose:**  
This test verifies whether a complex mental entity can be decomposed into its constituent parts.

**Query logic:**  
The query starts from `ex:Desire_Graduate` and follows one or more `bdi:hasPart` links:

```sparql
ex:Desire_Graduate bdi:hasPart+ ?part .
```

It then returns each part and its type.

**Expected result:**  
The expected result includes constituent beliefs and intentions, such as:

- `Belief_Employment`
- `Belief_GoodAtScience`
- `Intention_PassExams`
- `Intention_Graduation`
- `Intention_WriteThesis`

**Validation focus:**  
The test validates the use of `bdi:hasPart` for representing compositional mental entities.

---

## Test Case 4  `unit-test-4`

**Competency question:** What mental processes has an agent undergone?

**Purpose:**  
This test verifies which mental processes have been processed by the agent `ex:Mark`.

**Query logic:**  
The query retrieves processes connected to `ex:Mark` through `bdi:isProcessedBy`, and restricts the result to instances of `bdi:MentalProcess` or its subclasses.

```sparql
?process bdi:isProcessedBy ex:Mark .
?type rdfs:subClassOf* bdi:MentalProcess .
```

**Expected result:**  
The expected result includes:

- `BP_FailureRevision` as a `bdi:BeliefProcess`
- `DP_ResitDesire` as a `bdi:DesireProcess`
- `Planning_Graduate` as a `bdi:Planning`

**Validation focus:**  
The test validates the modelling of agent participation in mental processes.

---

## Test Case 5  `unit-test-5`

**Competency question:** What is the world state that a given mental state is about?

**Purpose:**  
This test checks whether mental states can be linked to the world states they refer to.

**Query logic:**  
The query retrieves mental states that use `bdi:refersTo` to point to a resource typed as `bdi:WorldState`.

```sparql
?mentalState bdi:refersTo ?worldState .
?worldState a bdi:WorldState .
```

**Expected result:**  
The expected result includes:

- `Belief_Employment` referring to `WS_AcademicCalendar`
- `Belief_ExamFailed` referring to `WS_ExamSchedule`

**Validation focus:**  
The test validates the intentional relation between mental states and world states.

---

## Test Case 6  `unit-test-6`

**Competency question:** What beliefs motivated the formation of a given desire?

**Purpose:**  
This test verifies which beliefs motivate the desire `ex:Desire_Graduate`.

**Query logic:**  
The query selects all instances of `bdi:Belief` that are connected to `ex:Desire_Graduate` by `bdi:motivates`.

```sparql
?belief a bdi:Belief .
?belief bdi:motivates ex:Desire_Graduate .
```

**Expected result:**  
The motivating beliefs are:

- `Belief_Employment`
- `Belief_GoodAtScience`
- `Belief_LovesPC`
- `Belief_LogicalSkills`

**Validation focus:**  
The test validates the motivational dependency from beliefs to desires.

---

## Test Case 7  `unit-test-7`

**Competency question:** Which desire does a particular intention fulfil?

**Purpose:**  
This test verifies the desire fulfilled by the intention `ex:Intention_PassExams`.

**Query logic:**  
The query follows the relation:

```sparql
ex:Intention_PassExams bdi:fulfils ?desire .
```

and checks that the target is a `bdi:Desire`.

**Expected result:**  
The expected desire is:

- `Desire_Graduate`

**Validation focus:**  
The test validates the fulfilment relation from intentions to desires.

---

## Test Case 8  `unit-test-8`

**Competency question:** Which mental process generated a given belief, desire, or intention?

**Purpose:**  
This test identifies the mental process that generated the belief `ex:Belief_ExamFailed`.

**Query logic:**  
The query follows:

```sparql
?process bdi:generates ex:Belief_ExamFailed .
```

and returns the process type.

**Expected result:**  
The expected process is:

- `BP_FailureRevision`, typed as `bdi:BeliefProcess`

**Validation focus:**  
The test validates the generative relation between mental processes and mental states.

---

## Test Case 9  `unit-test-9`

**Competency question:** When was a mental entity generated?

**Purpose:**  
This test retrieves the generation or occurrence time of mental entities.

**Query logic:**  
The query selects entities that are mental entities or subclasses thereof, then follows their temporal annotation:

```sparql
?entity bdi:atTime ?interval .
?interval bdi:hasStartTime ?instant .
?instant bdi:time ?timestamp .
```

**Expected result:**  
The expected result contains two main temporal groups:

1. Mental entities generated or valid from `2024-09-01T00:00:00`, including initial beliefs, the graduation desire, intentions, and planning.
2. Mental entities or processes associated with `2025-01-15T10:00:00`, including `Belief_ExamFailed`, `BP_FailureRevision`, `DP_ResitDesire`, `IP_ResitIntention`, and `Intention_ResitAlgorithms`.

**Validation focus:**  
The test validates temporal anchoring through `bdi:atTime`, `bdi:hasStartTime`, and `bdi:time`.

---

## Test Case 10  `unit-test-10`

**Competency question:** What triggered a mental process?

**Purpose:**  
This test verifies which mental entities trigger mental processes.

**Query logic:**  
The query restricts `?process` to instances of `bdi:MentalProcess` or its subclasses and follows `bdi:isTriggeredBy`.

```sparql
?process bdi:isTriggeredBy ?trigger .
?trigger a ?triggerType .
```

**Expected result:**  
The expected trigger is `Belief_ExamFailed`, which triggers:

- `BP_FailureRevision`
- `DP_ResitDesire`
- `IP_ResitIntention`

**Validation focus:**  
The test validates triggering relations from mental states to mental processes.

---

## Test Case 11  `unit-test-11`

**Competency question:** What justifications support a specific mental entity?

**Important note:**  
The competency question label and the SPARQL query do not appear to match. The question concerns justifications, but the query retrieves timestamps for mental entities. The query is effectively identical in intent to `unit-test-9`.

**Actual query purpose:**  
The query retrieves mental entities and their timestamps through `bdi:atTime`, `bdi:hasStartTime`, and `bdi:time`.

**Expected result:**  
The expected result lists mental entities and processes with timestamps, including:

- initial entities at `2024-09-01T00:00:00`
- later entities and processes at `2025-01-15T10:00:00`

**Validation focus:**  
As currently written, the test validates temporal anchoring, not justification support.

**Suggested correction:**  
To test the stated CQ, the query should instead use the justification relation, for example:

```sparql
SELECT ?justification ?entity
WHERE {
  ?justification a bdi:Justification ;
                 bdi:justifies ?entity .
}
```

or, for a specific mental entity:

```sparql
SELECT ?justification
WHERE {
  ?justification bdi:justifies ex:SomeMentalEntity .
}
```

---

## Test Case 12  `unit-test-12`

**Competency question:** What goal does a given intention or plan aim to fulfil?

**Purpose:**  
This test verifies the goal addressed by a plan.

**Query logic:**  
The query retrieves the goal addressed by `ex:Plan_Graduate`.

```sparql
ex:Plan_Graduate bdi:addresses ?goal .
?goal a bdi:Goal .
```

**Expected result:**  
The expected goal is:

- `Goal_GraduateCS`

**Validation focus:**  
The test validates the relation between plans and goals.

---

## Test Case 13  `unit-test-13`

**Competency question:** What plan has been specified by a particular intention?

**Purpose:**  
This test verifies which plan is specified by the intention `ex:Intention_PassExams`.

**Query logic:**  
The query follows:

```sparql
ex:Intention_PassExams bdi:specifies ?plan .
?plan a bdi:Plan .
```

**Expected result:**  
The expected plan is:

- `Plan_Graduate`

**Validation focus:**  
The test validates the relation between an intention and the plan it specifies.

---

## Test Case 14  `unit-test-14`

**Competency question:** What planning process led to the creation of a particular plan?

**Purpose:**  
This test identifies the planning process that defines the plan `ex:Plan_Graduate`.

**Query logic:**  
The query looks for an instance of `bdi:Planning` connected to `ex:Plan_Graduate` by `bdi:defines`.

```sparql
?planning a bdi:Planning .
?planning bdi:defines ex:Plan_Graduate .
```

**Expected result:**  
The expected planning process is:

- `Planning_Graduate`

**Validation focus:**  
The test validates the generation or definition of a plan by a planning process.

---

## Test Case 15  `unit-test-15`

**Competency question:** What is the ordered sequence of tasks that compose a given plan?

**Purpose:**  
This test verifies the ordered task structure of `ex:Plan_Graduate`.

**Query logic:**  
The query retrieves every task that is a component of `ex:Plan_Graduate` and optionally retrieves its immediate successor through `bdi:precedes`.

```sparql
ex:Plan_Graduate bdi:hasComponent ?task .
OPTIONAL { ?task bdi:precedes ?nextTask . }
```

**Expected result:**  
The plan contains the following sequence:

1. `Task_Enrol` precedes `Task_RegisterExam`
2. `Task_RegisterExam` precedes `Task_SitExam`
3. `Task_SitExam` precedes `Task_PayFees`
4. `Task_PayFees` precedes `Task_Graduation`
5. `Task_Graduation` has no successor

**Validation focus:**  
The test validates that plans can be represented as ordered sequences of tasks.

---

## Test Case 16  `unit-test-16`

**Competency question:** What is the temporal validity (start and end time) of a mental state?

**Note:**  
The competency question text contains a small typo: it ends with an extra `}`.

**Purpose:**  
This test retrieves the start and optional end time of mental states.

**Query logic:**  
The query selects resources typed as `bdi:MentalState` or one of its subclasses and retrieves their temporal interval.

```sparql
?state bdi:atTime ?interval .
?interval bdi:hasStartTime ?startInstant .
?startInstant bdi:time ?start .
OPTIONAL {
  ?interval bdi:hasEndTime ?endInstant .
  ?endInstant bdi:time ?end .
}
```

**Expected result:**  
The expected output includes mental states valid from `2024-09-01T00:00:00` to `2025-07-31T00:00:00`, such as:

- `Belief_Employment`
- `Belief_GoodAtScience`
- `Belief_LogicalSkills`
- `Belief_LovesPC`
- `Desire_Graduate`
- `Intention_Graduation`
- `Intention_PassExams`
- `Intention_WriteThesis`

It also includes open-ended states starting at `2025-01-15T10:00:00`, such as:

- `Belief_ExamFailed`
- `Intention_ResitAlgorithms`

**Validation focus:**  
The test validates temporal validity intervals, including open intervals without an end time.

---

## Test Case 17  `unit-test-17`

**Competency question:** What mental states were valid at a specific point in time?

**Purpose:**  
This test verifies which mental states were valid at the time `2024-10-01T00:00:00`.

**Query logic:**  
The query retrieves mental states whose start time is earlier than or equal to the target time and whose end time is either unbound or later than/equal to the target time.

```sparql
FILTER(?start <= ?t && (!BOUND(?end) || ?end >= ?t))
```

**Expected result:**  
The valid mental states at `2024-10-01T00:00:00` are:

- `Belief_Employment`
- `Belief_GoodAtScience`
- `Belief_LovesPC`
- `Belief_LogicalSkills`
- `Desire_Graduate`
- `Intention_PassExams`
- `Intention_WriteThesis`
- `Intention_Graduation`

**Validation focus:**  
The test validates point-in-time temporal reasoning over mental states.

---

## Test Case 18  `unit-test-18`

**Competency question:** How has a mental entity evolved over time?

**Purpose:**  
This test checks how the mental entity `ex:Desire_Graduate` has changed over time.

**Query logic:**  
The query checks whether any process generated, modified, or suppressed `ex:Desire_Graduate`, and labels the type of effect using `BIND`.

```sparql
?process bdi:generates ex:Desire_Graduate .
BIND("generates" AS ?affectType)
```

or:

```sparql
?process bdi:modifies ex:Desire_Graduate .
BIND("modifies" AS ?affectType)
```

or:

```sparql
?process bdi:suppresses ex:Desire_Graduate .
BIND("suppresses" AS ?affectType)
```

It then retrieves the time at which the process occurred.

**Expected result:**  
The expected evolution event is:

- `DP_ResitDesire` modifies `Desire_Graduate` at `2025-01-15T10:00:00`

**Validation focus:**  
The test validates diachronic reasoning over mental entities by tracking processes that affect them.

---

# Summary Table

| Test | Competency Question | Main construct tested |
|---|---|---|
| `unit-test-1` | What are mental entities? | `bdi:MentalEntity` taxonomy |
| `unit-test-2` | What mental states does an agent hold? | Agentâmental state relation |
| `unit-test-3` | What are the constituent mental entities? | Part-whole structure |
| `unit-test-4` | What mental processes has an agent undergone? | Agentâprocess participation |
| `unit-test-5` | What world state is a mental state about? | Mental state reference |
| `unit-test-6` | What beliefs motivated a desire? | Beliefâdesire motivation |
| `unit-test-7` | Which desire does an intention fulfil? | Intentionâdesire fulfilment |
| `unit-test-8` | Which process generated a mental state? | Process generation |
| `unit-test-9` | When was a mental entity generated? | Temporal anchoring |
| `unit-test-10` | What triggered a mental process? | Triggering relation |
| `unit-test-11` | What justifications support a mental entity? | Mismatch: currently tests temporal anchoring |
| `unit-test-12` | What goal does a plan aim to fulfil? | Planâgoal relation |
| `unit-test-13` | What plan has been specified by an intention? | Intentionâplan relation |
| `unit-test-14` | What planning process created a plan? | Planningâplan definition |
| `unit-test-15` | What is the ordered task sequence? | Ordered tasks in plans |
| `unit-test-16` | What is the temporal validity of a mental state? | Start/end temporal validity |
| `unit-test-17` | What mental states were valid at a time? | Point-in-time validity |
| `unit-test-18` | How has a mental entity evolved over time? | Mental entity evolution |


