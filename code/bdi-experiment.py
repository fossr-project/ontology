import openai
import json
import time
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class BDIValidationTester:
    def __init__(self, api_key: str, ontology_file_path: str):
        """
        Initialize the BDI validation tester.

        Args:
            api_key: OpenAI API key
            ontology_file_path: Path to your BDI ontology RDF file
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.ontology_content = self._load_ontology(ontology_file_path)
        self.results = []

    def _load_ontology(self, file_path: str) -> str:
        """Load the BDI ontology from RDF file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded ontology from {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error loading ontology: {e}")
            raise

    def _call_openai(self, prompt: str, include_ontology: bool = True) -> str:
        """
        Make API call to OpenAI with or without ontology.

        Args:
            prompt: The test prompt
            include_ontology: Whether to include BDI ontology in system message
        """
        try:
            system_message = self._get_system_message(include_ontology)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error: {e}"

    def _get_system_message(self, include_ontology: bool) -> str:
        """Generate system message with or without ontology."""
        base_message = """You are an expert in analyzing agent behavior and mental states from task data. 
Provide detailed, structured analysis of the given scenarios."""

        if include_ontology:
            ontology_message = f"""You are an expert in BDI (Belief-Desire-Intention) agent reasoning. Use the following BDI ontology to analyze agent mental states systematically along with possible constraints. Output RDF triples from the data you have according to the ontology.

BDI ONTOLOGY:
{self.ontology_content}

When analyzing tasks and agent behavior, use BDI ontology concepts including:
- Agent: autonomous entity with mental states
- Belief: what agent holds to be true about the world
- Desire: motivational preferences/goals
- Intention: commitment to achieve specific goals
- MentalProcess: belief/desire/intention formation processes
- Justification: rationale supporting mental states
- Goal: desired outcomes
- Plan: structured action sequences
- TemporalEntity: time-related aspects
- Proposition: content of mental states

Provide structured analysis using these BDI concepts and their relationships. """
            return ontology_message

        return base_message

    def run_test(self, test_name: str, test_data: str, query: str) -> Dict:
        """
        Run a single test case with and without ontology.

        Args:
            test_name: Name of the test
            test_data: Task data for the test
            query: Question to ask about the data

        Returns:
            Dictionary with test results
        """
        logger.info(f"Running test: {test_name}")

        full_prompt = f"""Task Data:
{test_data}

Query: {query}

Please provide your analysis."""

        # Test without ontology
        logger.info("Testing WITHOUT ontology...")
        response_without = self._call_openai(full_prompt, include_ontology=False)
        time.sleep(1)  # Rate limiting

        # Test with ontology
        logger.info("Testing WITH ontology...")
        response_with = self._call_openai(full_prompt, include_ontology=True)
        time.sleep(1)  # Rate limiting

        result = {
            'test_name': test_name,
            'test_data': test_data,
            'query': query,
            'response_without_ontology': response_without,
            'response_with_ontology': response_with
        }

        self.results.append(result)
        return result

    def test_1_location_contradiction(self):
        """Test 1: Location-Task Contradiction Detection"""
        test_data = """ID: 12693542, Task: "check into hotel", Location: "home", Time: "WE-morning"
ID: 10169250, Task: "buy new water filters", Location: "work", Time: "WD-evening"
ID: 5030401, Task: "workflow meeting", Location: "public", Time: 'WD-afternoon'"""

        query = "Are these task-location combinations logically consistent? Identify and explain any contradictions you detect."

        return self.run_test("Location Contradiction Detection", test_data, query)

    def test_2_temporal_evolution(self):
        """Test 2: Temporal Mental State Evolution"""
        test_data = """Monday: "check email rules" at home,work during WD-morning
Tuesday: "email prof about class" at home,work during WD-afternoon
Wednesday: "respond to andy" at home,work during WD-evening"""

        query = "Trace the agent's mental state evolution across these three days. "

        return self.run_test("Temporal Mental State Evolution", test_data, query)

    def test_3_intention_plan_consistency(self):
        """Test 3: Intention-Plan Consistency"""
        test_data = """Agent Intention: "Maintain household cleanliness"

        Proposed Tasks:
        - "vacuum guest room" at home during WE-morning
        - "leave money for cleaners" at home during WD-morning
        - "check into hotel" at public during WE-morning        
        - "organize living room" at home during WE-afternoon
        - "dust shelves" at home during WE-evening              
        """

        query = "Which of these tasks support the stated intention? Identify any inconsistent tasks and explain why they don't align with the intention."

        return self.run_test("Intention-Plan Consistency", test_data, query)

    def test_4_justification_analysis(self):
        """Test 4: Belief-Desire-Intention Justification Analysis"""
        test_data = """Task: "cancel rental car" at home,work during WD-anytime"""

        query = "What beliefs must the agent hold to form this intention? What desire does it fulfill? Provide the complete justification chain for this mental state."

        return self.run_test("Justification Analysis", test_data, query)

    def test_5_mental_state_attribution(self):
        """Test 5: Mental State Attribution"""
        test_data = """Task Set:
        - "transfer credit-card balance" at home during WD-evening
        - "pay ghadah" at home during WE-afternoon
        - "email mary lynn" at work during WD-morning
        """

        query = "What mental states does this agent have regarding financial management? How do these tasks relate to each other?"

        return self.run_test("Mental State Attribution", test_data, query)

    def test_6_temporal_validity_conflict(self):
        """Test 6: Temporal Validity Conflict"""
        test_data = """Agent beliefs: "Banks are closed after 5 PM"
Agent intention: "deposit checks at chase during WD-evening" """

        query = "Can these mental states coexist?"

        return self.run_test("Temporal Validity Conflict", test_data, query)

    def test_7_concurrent_intentions(self):
        """Test 7: Mental State Concurrency"""
        test_data = """Belief: "The agent can only attend one meeting at a time"

        Tasks scheduled for WD-afternoon:
        - "workflow meeting" at work
        - "email prof about class" at work
        - "check email rules" at work
        """

        query = "Can an agent simultaneously hold all these intentions for the same time period?"

        return self.run_test("Concurrent Intentions Analysis", test_data, query)

    def test_8_goal_hierarchy(self):
        """Test 8: Goal Decomposition and Hierarchy"""
        test_data = """Task Collection:
- "paint pink room" at home during WE-morning
- "organize guest room closet" at home during WD-evening
- "vacuum guest room" at home during WE-morning
- "organize living room" at home during WE-afternoon"""

        query = "What higher-level goal unifies these intentions? Construct the goal hierarchy and explain the relationships between tasks."

        return self.run_test("Goal Hierarchy Analysis", test_data, query)

    def test_9_plan_specification(self):
        """Test 9: Plan Specification from Intentions"""
        test_data = """Intention: "Prepare for academic success"

Available Tasks:
- "email prof about class"
- "upload instagram"
- "calc quiz sunday"  
- "physics packet"
- "history exam"
- "check email rules" """

        query = "Which tasks support this intention?"

        return self.run_test("Plan Specification", test_data, query)

    def test_10_impossible_simultaneous_states(self):
        """Test 10: Impossible Simultaneous Mental States"""
        test_data = '''Agent Mental State Profile:

        Beliefs:
        - "On Fridays I must remain online from 13:00-17:00 for remote customer support"
        - "Important workshops require my physical presence"

        Intentions (both for Friday WD-afternoon):
        - "attend in-person workshop 14:00-16:00"
        - "organize living room 15:00-17:00" '''

        query = "What contradictions exist in this agent's mental state?"

        return self.run_test("Impossible Simultaneous States", test_data, query)

    def test_11_severe_contradictions(self):
        """Test 11: Severe Location-Task Contradictions"""
        test_data = '''ID: 999001, Task: "check into hotel", Location: "home", Time: "WE-morning"
    ID: 999002, Task: "get haircut", Location: "home", Time: "WD-evening"  
    ID: 999003, Task: "pump gas", Location: "home", Time: "WD-morning"
    ID: 999004, Task: "renew driver's license", Location: "home", Time: "WD-afternoon"'''

        query = "Analyze these task-location combinations. How many contradictions exist and why?"

        return self.run_test("Severe Location Contradictions", test_data, query)


    def test_11_severe_contradictions(self):
        test_data = """ID: 999001, Task: "check into hotel", Location: "home", Time: "WE-morning"
    ID: 999002, Task: "get haircut", Location: "home", Time: "WD-evening"
    ID: 999003, Task: "pump gas", Location: "home", Time: "WD-morning"
    ID: 999004, Task: "renew driver's license", Location: "home", Time: "WD-afternoon"
    ID: 999005, Task: "attend wedding ceremony", Location: "work", Time: "WE-afternoon"
    ID: 999006, Task: "buy groceries", Location: "work", Time: "WD-afternoon"""

        query = "Analyze these task-location combinations. How many contradictions exist and why?"

        return self.run_test("Severe Location Contradictions", test_data, query)

    def test_12_business_hours_violations(self):
        """Test 12: Business Hours Temporal Contradictions"""
        test_data = """Agent beliefs: 
    - "Banks close at 5 PM"
    - "DMV offices close at 6 PM" 
    - "Doctor offices close at 7 PM"
    - "Hair salons close at 8 PM"

    Agent intentions:
    - "deposit checks at bank during WD-night"
    - "renew registration at DMV during WE-night"
    - "schedule doctor appointment during WD-night"
    - "get haircut during WD-night" """

        query = "Identify all temporal contradictions between the agent's beliefs and intentions."

        return self.run_test("Business Hours Contradictions", test_data, query)

    def test_13_physical_impossibilities(self):
        """Test 13: Simultaneous Physical Impossibilities"""
        test_data = """Agent intentions for WD-afternoon (14:00-15:00, same slot):
        - "chair team video-call (online)"
        - "get haircut (requires being at salon)"
        - "vacuum living room (requires being at home)"
        - "deposit checks via drive-through bank"
        - "3-D-print parts (requires being at maker-lab)"
        """


        query = "Can one agent fulfill all these intentions simultaneously?"

        return self.run_test("Physical Impossibilities", test_data, query)

    def test_14_resource_constraint_violations(self):
        """Test 14: Resource and Context Violations"""
        test_data = """ID: 999007, Task: "3-D-print parts", ResourceNeeded: "3-D printer", ResourceOwned: "no", Time: "WD-afternoon"
        ID: 999008, Task: "mow lawn", Condition: "heavy rain forecast", Time: "WD-morning"
        ID: 999009, Task: "cook dinner", ResourceNeeded: "kitchen access", ResourceLocation: "work office", Time: "WD-evening"
        ID: 999010, Task: "take shower", ResourceNeeded: "private bathroom", Context: "public park", Time: "WD-morning"
        ID: 999011, Task: "sleep 8 hours", Context: "open-plan office", Time: "WD-afternoon"
        ID: 999012, Task: "vacuum guest room", ResourceNeeded: "vacuum cleaner", ResourceOwned: "no", Time: "WE-morning"
        """


        query = "Which of these tasks violate resource availability?"

        return self.run_test("Resource Constraint Violations", test_data, query)

    def test_15_complex_belief_intention_conflicts(self):
        """Test 15: Complex Belief-Intention Contradiction Matrix"""
        test_data = """Agent Mental State Profile:

    Beliefs:
    - "I work remotely on Fridays"
    - "Banks close at 5 PM on weekdays"
    - "I don't own a car"
    - "My apartment has no garage"
    - "I'm vegetarian"
    - "Gyms require membership"

    Intentions:
    - "attend in-person meeting at office during Friday WD-afternoon"
    - "deposit cash at bank during Friday WD-evening"
    - "drive to grocery store during Friday WD-morning"
    - "park car in garage during Friday WD-evening"
    - "order steak dinner during Friday WD-evening"
    - "workout at gym during Friday WD-night" """

        query = "How many belief-intention contradictions exist in this agent's mental state? Rank them by severity."

        return self.run_test("Complex Belief-Intention Conflicts", test_data, query)

    def test_16_cascading_impossibilities(self):
        """Test 16: Cascading Logical Impossibilities"""
        test_data = """Sequential Task Dependencies:

        Step 1: "enrol in online course before WE-morning"
        Step 2: "complete prerequisite assessment online during WE-morning" (depends on 1)
        Step 3: "attend live webinar online during WE-afternoon" (depends on 2)
        Step 4: "submit practical assignment that requires a valid driver's licence during WE-evening" (depends on 3)
        Step 5: "receive digital certificate during WE-night" (depends on 4)

        Agent beliefs:
        - "I do not hold a driver’s licence"
        - "My internet connection is unreliable after 18:00"
        """


        query = "Analyze this task sequence for cascading logical failures. "

        return self.run_test("Cascading Impossibilities", test_data, query)

    def test_cq9_invoice_trigger(self):
            """CQ-9: What external event triggered the mental process?"""
            test_data = """
    ExternalEvent: At 10:15 AM a push-notification from the banking app says: “Ghadeh has requested $250 via Zelle.”
    MentalProcess: The agent deliberates whether and how to send the money.
    CandidateTask:
      - ID: 11439167
        Task: "pay ghadah"
        SuggestedTime: "WE-afternoon"
    """
            query = (
                "Which external event triggered the mental process that resulted in the intention "
                "encoded by Task 11439167?"
            )
            return self.run_test("CQ9 - Invoice-Triggered Payment", test_data, query)

    def test_cq12_meal_planning(self):
            """CQ-12: What planning process produced the plan?"""
            test_data = """
    PlanningProcess: During the family’s regular 11 AM Sunday “Meal-Planning Huddle”, everyone decides on dinners for the coming week.
    ResultingPlan:
      - ID: 6015973
        Task: "make meal plans"
        SuggestedTime: "WD-afternoon"
    """
            query = (
                "Identify the planning process that produced Plan 6015973 and encode their relationship "
                "."
            )
            return self.run_test("CQ12 - Sunday Meal-Planning Session", test_data, query)

    def run_subset(self, methods):
        """Run only the test methods passed in as a list."""
        subset_results = []
        for m in methods:
            subset_results.append(m())
            logger.info(f"Completed subset test: {m.__name__}")
        return subset_results

    def run_all_tests(self):
        """Run all validation tests including controversial scenarios."""
        logger.info("Starting Enhanced BDI Ontology Validation Tests...")

        test_methods = [
            self.test_1_location_contradiction,
            self.test_2_temporal_evolution,
            self.test_3_intention_plan_consistency,
            self.test_4_justification_analysis,
            self.test_5_mental_state_attribution,
            self.test_6_temporal_validity_conflict,
            self.test_7_concurrent_intentions,
            self.test_8_goal_hierarchy,
            self.test_9_plan_specification,
            self.test_10_impossible_simultaneous_states,
            self.test_12_business_hours_violations,
            self.test_13_physical_impossibilities,
            self.test_14_resource_constraint_violations,
            self.test_15_complex_belief_intention_conflicts,
            self.test_16_cascading_impossibilities
        ]

        for test_method in test_methods:
            try:
                test_method()
                logger.info(f"Completed: {test_method.__name__}")
            except Exception as e:
                logger.error(f"Failed: {test_method.__name__} - {e}")

        logger.info("All enhanced tests completed!")
        return self.results

    def save_results(self, output_file: str = "bdi_validation_results.json"):
        """Save test results to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_file}")

    def generate_comparison_report(self, output_file: str = "bdi_comparison_report.html"):
        """Generate HTML comparison report."""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>BDI Ontology Validation Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .test { border: 1px solid #ccc; margin: 20px 0; padding: 15px; }
        .test-name { font-size: 18px; font-weight: bold; color: #333; }
        .test-data { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        .query { background: #e8f4fd; padding: 10px; margin: 10px 0; }
        .response { margin: 10px 0; }
        .without-ontology { background: #fff2f2; padding: 10px; }
        .with-ontology { background: #f2fff2; padding: 10px; }
        .comparison { background: #fffacd; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>BDI Ontology Validation Results</h1>
    <p>This report compares LLM responses with and without the BDI ontology to demonstrate enhanced reasoning capabilities.</p>
"""

        for i, result in enumerate(self.results, 1):
            html_content += f"""
    <div class="test">
        <div class="test-name">Test {i}: {result['test_name']}</div>

        <div class="test-data">
            <strong>Test Data:</strong><br>
            <pre>{result['test_data']}</pre>
        </div>

        <div class="query">
            <strong>Query:</strong><br>
            {result['query']}
        </div>

        <div class="response">
            <h4>Response WITHOUT Ontology:</h4>
            <div class="without-ontology">{result['response_without_ontology']}</div>
        </div>

        <div class="response">
            <h4>Response WITH BDI Ontology:</h4>
            <div class="with-ontology">{result['response_with_ontology']}</div>
        </div>

        <div class="comparison">
            <strong>Key Differences:</strong> The ontology-enhanced response should show more structured reasoning using BDI concepts, better consistency checking, and systematic mental state analysis.
        </div>
    </div>
"""

        html_content += """
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Comparison report saved to {output_file}")


def main():
    """Main execution function."""
    # Configuration
    API_KEY = "mykey"
    ONTOLOGY_FILE = "bdi-v0.2.rdf"

    # Initialize tester
    tester = BDIValidationTester(API_KEY, ONTOLOGY_FILE)

    # Run all tests
    results = tester.run_all_tests()

    # Save results
    tester.save_results()
    tester.generate_comparison_report()

    # Print summary
    print(f"\nValidation Complete!")
    print(f"Total tests run: {len(results)}")
    print(f"Results saved to: bdi_validation_results.json")
    print(f"Comparison report: bdi_comparison_report.html")


if __name__ == "__main__":
    main()