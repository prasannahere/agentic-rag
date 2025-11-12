"""
Demo script to test the Answer Verification Agent.

This shows how to use the verifier to critically evaluate answers.
"""

from verifier import AnswerVerificationAgent


def test_verification():
    """Test the verification agent with various scenarios"""
    
    # Initialize the verifier
    verifier = AnswerVerificationAgent()
    
    # Test Case 1: Good, complete answer
    print("\n" + "="*80)
    print("TEST CASE 1: Good Answer")
    print("="*80)
    question1 = "How do I reset my password?"
    answer1 = """To reset your password:
    1. Go to the login page and click 'Forgot Password'
    2. Enter your email address
    3. Check your email for the reset link (valid for 24 hours)
    4. Click the link and create a new password (must be 8+ characters with uppercase, lowercase, and numbers)
    5. Log in with your new password
    
    If you don't receive the email within 15 minutes, contact IT support at itsupport@company.com or call ext. 5555."""
    
    result1 = verifier.verify_answer(question1, answer1)
    print(f"\nResult: {result1}")
    
    # Test Case 2: Vague, incomplete answer
    print("\n" + "="*80)
    print("TEST CASE 2: Vague Answer")
    print("="*80)
    question2 = "How do I request SSL certificate renewal?"
    answer2 = """You need to contact the relevant team and follow the standard procedure. 
    Make sure you have the necessary approvals and submit the required forms."""
    
    result2 = verifier.verify_answer(question2, answer2)
    print(f"\nResult: {result2}")
    
    # Test Case 3: Irrelevant answer
    print("\n" + "="*80)
    print("TEST CASE 3: Irrelevant Answer")
    print("="*80)
    question3 = "What is the SAP access request process?"
    answer3 = """SAP is an enterprise resource planning software that helps businesses 
    manage their operations. It was founded in Germany in 1972 and is used by many 
    Fortune 500 companies worldwide."""
    
    result3 = verifier.verify_answer(question3, answer3)
    print(f"\nResult: {result3}")
    
    # Test Case 4: Partially correct answer
    print("\n" + "="*80)
    print("TEST CASE 4: Partially Correct Answer")
    print("="*80)
    question4 = "Who handles access requests for Office 365?"
    answer4 = """Access requests are handled by the IT department. You need to submit 
    a ticket through the portal."""
    
    result4 = verifier.verify_answer(question4, answer4)
    print(f"\nResult: {result4}")


if __name__ == "__main__":
    test_verification()

