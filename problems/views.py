from django.shortcuts import render
from registration.models import User
from .models import Problem
from .models import Submission, TestCase
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseForbidden
from django.db.models import Count, Avg, Sum, F
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .forms import *
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt
import json
import sys
import subprocess
import tempfile
import os
import time
import signal
import psutil
import threading
import time
from .gemini_service import GeminiService
import json
from django.http import JsonResponse

# Create your views here.
@login_required(login_url='login')
@never_cache
def render_homepage(request, id):
    user = get_object_or_404(User, id=id)

    if request.method == 'POST' and request.FILES.get('profile_photo'):
        user.profile_photo = request.FILES['profile_photo']
        user.save()


    user_submissions = Submission.objects.filter(user=user)
    

    solved_problems = user_submissions.filter(
        verdict='Accepted'  
    ).values('problem').distinct()
    
    solved_count = solved_problems.count()
    

    attempted_problems = user_submissions.values('problem').distinct().count()
    

    total_submissions = user_submissions.count()
    
    accuracy = round((solved_count / total_submissions) * 100, 2) if attempted_problems > 0 else 0

    language_stats = user_submissions.values('language').annotate(
        count=Count('id')
    ).order_by('-count')
    
 
    difficulty_stats = []
    for difficulty in ['Easy', 'Medium', 'Hard']:
        count = solved_problems.filter(problem__difficulty=difficulty).count()
        difficulty_stats.append({
            'difficulty': difficulty,
            'count': count
        })
    

    recent_submissions = user_submissions.order_by('-submitted_at')[:5]
    
    return render(request, "profile.html", {
        'user': user,
        'solved_count': solved_count,
        'accuracy': accuracy,
        'total_submissions': total_submissions,
        'attempted_problems': attempted_problems,
        'language_stats': language_stats,
        'difficulty_stats': difficulty_stats,
        'recent_submissions': recent_submissions,
    })


@login_required(login_url='login')
@never_cache
def render_problemspage(request, id):
    user = get_object_or_404(User, id=id)
    problems = Problem.objects.all()
    try:
        solved_problem_ids = Submission.objects.filter(
            user=user,
            verdict='Accepted'  # Adjust this based on your status choices
        ).values_list('problem_id', flat=True).distinct()
        
        # Convert QuerySet to list for template usage
        solved_problem_ids = list(solved_problem_ids)
    except:
        # If Submission model doesn't exist or has issues, use empty list
        solved_problem_ids = []
    print(solved_problem_ids)
    return render(request, "problems.html", {
        'user': user,
        'problems': problems,
        'solved_problem_ids': solved_problem_ids,
    })

@login_required
def delete_profile(request, id):
    # Get the user to delete
    user_to_delete = get_object_or_404(User, id=id)
    
    # Security check - only allow users to delete their own profile
    if request.user != user_to_delete:
        raise Http404("You can only delete your own profile")
    
    if request.method == 'POST':
        # Log the user out before deletion
        from django.contrib.auth import logout
        logout(request)
        request.session.flush()
        
        # Delete the user
        user_to_delete.delete()
        
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('signup')# Redirect to homepage
    
    # If GET request, redirect back to profile
    return redirect('user-details', id=id)

@login_required
def add_problem(request, id):
    user = request.user
    if not (user.is_superuser or (user.is_community_user and user.is_approved)):
        return HttpResponseForbidden("You are not allowed to add problems.")

    if request.method == 'POST':
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.created_by = user
            problem.save()

            # ✅ Parse testcases from hidden field
            testcases_raw = form.cleaned_data.get('testcases', '[]')
            try:
                testcases_data = json.loads(testcases_raw)
                for tc in testcases_data:
                    TestCase.objects.create(
                        problem=problem,
                        input=tc.get('input', ''),
                        expected_output=tc.get('expected_output', ''),
                        is_sample=tc.get('is_sample', False)
                    )
            except json.JSONDecodeError:
                messages.error(request, "Failed to parse test cases.")

            messages.success(request, 'Problem added successfully!')
            return redirect('problems-page', id=id)
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = ProblemForm()

    return render(request, 'add_problems.html', {'form': form})

@login_required(login_url='login')
@never_cache
def problems_list(request):
    problems = Problem.objects.all().order_by('-id')  # Show newest first
    
    # Filter by difficulty if requested
    difficulty = request.GET.get('difficulty')
    if difficulty and difficulty in ['Easy', 'Medium', 'Hard']:
        problems = problems.filter(difficulty=difficulty)
    
    # You can add more filtering logic here
    context = {
        'problems': problems,
        'user': request.user,
    }
    return render(request, 'problems.html', context)


@login_required
def approve_users(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Admins only.")

    pending_users = User.objects.filter(is_community_user=True, is_approved=False)
    approved_users = User.objects.filter(is_community_user=True, is_approved=True)

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        try:
            user = User.objects.get(id=user_id)
            if action == "approve":
                user.is_approved = True
                user.save()
            elif action == "reject":
                user.is_community_user = False
                user.is_approved = False
                user.save()
            elif action == "remove":
                user.is_community_user = False
                user.is_approved = False
                user.save()
        except User.DoesNotExist:
            pass

        return redirect("approve-users")

    return render(request, "approve_users.html", {
        "pending_users": pending_users,
        "approved_users": approved_users
    })
def solve_problem(request, id, problem_id):
    user = get_object_or_404(User, id=id)
    problem = get_object_or_404(Problem, id=problem_id)
    
    # You can add code templates for different languages
    code_templates = {
        'python': getattr(problem, 'python_template', None) or "# Write your Python solution here",
        'javascript': getattr(problem, 'javascript_template', None) or "// Write your JavaScript solution here", 
        'java': getattr(problem, 'java_template', None) or "// Write your Java solution here",
        'cpp': getattr(problem, 'cpp_template', None) or "// Write your C++ solution here",
        'c': getattr(problem, 'c_template', None) or "// Write your C solution here"
    }
    
    context = {
        'user': user,
        'problem': problem,
        'code_templates': code_templates,
    }
    return render(request, 'solve-problem.html', context)

# Code execution timeout (in seconds)
EXECUTION_TIMEOUT = 10

def create_temp_file(code, language):
    """Create a temporary file with the given code"""
    extensions = {
        'python': '.py',
        'javascript': '.js',
        'java': '.java',
        'cpp': '.cpp',
        'c': '.c'
    }
    
    suffix = extensions.get(language, '.txt')
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    temp_file.write(code)
    temp_file.close()
    return temp_file.name

def get_execution_command(language, file_path):
    """Get the command to execute code based on language"""
    commands = {
        'python': ['python3', file_path],
        'javascript': ['node', file_path],
        'java': ['javac', file_path, '&&', 'java', '-cp', os.path.dirname(file_path), 
                os.path.basename(file_path).replace('.java', '')],
        'cpp': ['g++', '-o', file_path.replace('.cpp', ''), file_path, '&&', file_path.replace('.cpp', '')],
        'c': ['gcc', '-o', file_path.replace('.c', ''), file_path, '&&', file_path.replace('.c', '')]
    }
    return commands.get(language, ['echo', 'Language not supported'])

def execute_code_safely(code, language, test_input="", timeout=EXECUTION_TIMEOUT):
    """Execute code safely with timeout, input and memory monitoring (Windows compatible)"""
    try:
        # Create temporary file
        temp_file = create_temp_file(code, language)
        
        # Get execution command  
        start_time = time.time()
        memory_tracker = {'peak': 0}

        if language in ['java', 'cpp', 'c', 'python']:
            # For compiled languages, compile first
            if language == 'java':
                compile_cmd = ['javac', temp_file]
                compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=timeout)
                if compile_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Compilation Error:\n{compile_result.stderr}',
                        'runtime': 0
                    }
                # Run the compiled code
                class_name = os.path.basename(temp_file).replace('.java', '')
                run_cmd = ['java', '-cp', os.path.dirname(temp_file), class_name]
            elif language == 'cpp':
                exe_file = temp_file.replace('.cpp', '')
                compile_cmd = ['g++', '-o', exe_file, temp_file]
                compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=timeout)
                if compile_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Compilation Error:\n{compile_result.stderr}',
                        'runtime': 0
                    }
                run_cmd = [exe_file]
            elif language == 'c':
                exe_file = temp_file.replace('.c', '')
                compile_cmd = ['gcc', '-o', exe_file, temp_file]
                compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=timeout)
                if compile_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Compilation Error:\n{compile_result.stderr}',
                        'runtime': 0
                    }
                run_cmd = [exe_file]
            elif language == 'python':
                run_cmd = [sys.executable, temp_file]
        else:
            # For interpreted languages
            run_cmd = cmd
        # [Keep existing compilation logic for java, cpp, c]
        
        # Execute the code with memory monitoring
        process = subprocess.Popen(
            run_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Start memory monitoring in separate thread
        memory_thread = threading.Thread(
            target=monitor_memory_usage, 
            args=(psutil.Process(process.pid), memory_tracker)
        )
        memory_thread.daemon = True
        memory_thread.start()
        
        try:
            stdout, stderr = process.communicate(input=test_input, timeout=timeout)
            memory_thread.join(timeout=0.1)  # Wait briefly for thread to finish
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return {
                'success': False,
                'error': f'Time Limit Exceeded (>{timeout}s)',
                'runtime': timeout * 1000,
                'memory_used': memory_tracker['peak']
            }
        
        execution_time = time.time() - start_time
        
        # Clean up temporary files
        try:
            os.unlink(temp_file)
            if language in ['java', 'cpp', 'c']:
                # Clean up compiled files
                if language == 'java':
                    class_file = temp_file.replace('.java', '.class')
                    if os.path.exists(class_file):
                        os.unlink(class_file)
                elif language in ['cpp', 'c']:
                    exe_file = temp_file.replace(f'.{language}', '')
                    if os.path.exists(exe_file):
                        os.unlink(exe_file)
        except:
            pass
        
        if process.returncode == 0:
            return {
                'success': True,
                'output': stdout,
                'runtime': round(execution_time * 1000, 2),
                'memory_used': round(memory_tracker['peak'], 2)
            }
        else:
            return {
                'success': False,
                'error': f'Runtime Error:\n{stderr}',
                'runtime': round(execution_time * 1000, 2),
                'memory_used': round(memory_tracker['peak'], 2)
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Execution Error: {str(e)}',
            'runtime': 0,
            'memory_used': 0
        }

def run_test_cases(code, language, test_cases):
    """Run code against multiple test cases"""
    results = []
    total_runtime = 0
    passed_count = 0
    total_memory = 0
    
    for i, test_case in enumerate(test_cases):
        test_input = test_case.get('input', '')
        expected_output = test_case.get('expected_output', '').strip()
        
        result = execute_code_safely(code, language, test_input)
        
        if result['success']:
            actual_output = result['output'].strip()
            is_correct = actual_output == expected_output
            
            if is_correct:
                passed_count += 1
            
            results.append({
                'test_case': i + 1,
                'input': test_input,
                'expected': expected_output,
                'actual': actual_output,
                'passed': is_correct,
                'runtime': result['runtime'],
                'memory_used': result.get('memory_used', 0) 
            })
            total_runtime += result['runtime']
            total_memory = max(total_memory, result.get('memory_used', 0))
        else:
            results.append({
                'test_case': i + 1,
                'input': test_input,
                'expected': expected_output,
                'actual': '',
                'passed': False,
                'error': result['error'],
                'runtime': result['runtime'],
                'memory_used': result.get('memory_used', 0)
            })
            total_runtime += result['runtime']
            total_memory = max(total_memory, result.get('memory_used', 0))
            break  # Stop on first error
    
    return {
        'results': results,
        'passed_count': passed_count,
        'total_count': len(test_cases),
        'total_runtime': total_runtime,
        'peak_memory': total_memory,
        'all_passed': passed_count == len(test_cases)
    }

@csrf_exempt
@login_required
def run_code(request, id, problem_id):
    """Run code with sample test cases"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=id)
            problem = get_object_or_404(Problem, id=problem_id)
            
            # Check if user has permission to access this problem
            if request.user.id != user.id and not request.user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
            
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            language = data.get('language', 'python')
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'error': 'No code provided'
                })
            
            # Get sample test cases (usually 2-3 examples shown to user)
            # sample_test_cases = [
            #     {
            #         'input': '2 7 11 15\n9',
            #         'expected_output': '0 1'
            #     },
            #     {
            #         'input': '3 2 4\n6', 
            #         'expected_output': '1 2'
            #     }
            # ]
            
            # If you have a TestCase model, you can get them from database:
            sample_test_cases = list(problem.testcases.filter(is_sample=True).values('input', 'expected_output'))
            
            # Run the test cases
            test_results = run_test_cases(code, language, sample_test_cases)
            
            # Format output for display
            output_lines = []
            
            for result in test_results['results']:
                output_lines.append(f"Test Case {result['test_case']}:")
                output_lines.append(f"Input: {result['input']}")
                output_lines.append(f"Expected: {result['expected']}")
                output_lines.append(f"Your Output: {result['actual']}")
                
                if result['passed']:
                    output_lines.append("✓ Passed")
                else:
                    if 'error' in result:
                        output_lines.append(f"✗ Failed - {result['error']}")
                    else:
                        output_lines.append("✗ Failed - Wrong Answer")
                
                output_lines.append(f"Runtime: {result['runtime']}ms")
                output_lines.append("")
            
            output_lines.append(f"Summary: {test_results['passed_count']}/{test_results['total_count']} test cases passed")
            output_lines.append(f"Total Runtime: {test_results['total_runtime']:.2f}ms")
            
            return JsonResponse({
                'success': True,
                'output': '\n'.join(output_lines),
                'passed_count': test_results['passed_count'],
                'total_count': test_results['total_count']
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@csrf_exempt
@login_required  
def submit_code(request, id, problem_id):
    """Submit code for final evaluation"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=id)
            problem = get_object_or_404(Problem, id=problem_id)
            
            # Check permissions
            if request.user.id != user.id and not request.user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
            
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            language = data.get('language', 'python')
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'error': 'No code provided'
                })
            
            # Get all test cases (including hidden ones)
            # all_test_cases = [
            #     {'input': '2 7 11 15\n9', 'expected_output': '0 1'},
            #     {'input': '3 2 4\n6', 'expected_output': '1 2'},
            #     {'input': '3 3\n6', 'expected_output': '0 1'},
            #     # Add more hidden test cases
            #     {'input': '1 2 3 4 5\n8', 'expected_output': '2 4'},
            #     {'input': '5 5 5 5\n10', 'expected_output': '0 1'},
            # ]
            
            # If you have a TestCase model:
            all_test_cases = list(problem.testcases.all().values('input', 'expected_output'))
            
            # Run all test cases
            test_results = run_test_cases(code, language, all_test_cases)
            
            # Calculate score and verdict
            if test_results['all_passed']:
                verdict = 'Accepted'
                score = 100
            elif test_results['passed_count'] > 0:
                verdict = 'Partially Correct'
                score = (test_results['passed_count'] / test_results['total_count']) * 100
            else:
                verdict = 'Wrong Answer'
                score = 0
            
            # Save submission to database (only if Submission model exists)
# Replace your try-except block with this for debugging:

            # Save submission to database with detailed error handling
            try:
                print("=== DEBUGGING SUBMISSION CREATION ===")
                print(f"User: {user}")
                print(f"Problem: {problem}")
                print(f"Code length: {len(code) if code else 'None'}")
                print(f"Language: {language}")
                print(f"Verdict: {verdict}")
                print(f"Score: {score}")
                print(f"Test results: {test_results}")
                
                # Check if all required fields are present
                if not user:
                    raise ValueError("User is None")
                if not problem:
                    raise ValueError("Problem is None")
                if not code:
                    raise ValueError("Code is empty")   
                if not language:
                    raise ValueError("Language is empty")
                
                submission = Submission.objects.create(
                    user=user,
                    problem=problem,
                    code=code,
                    language=language,
                    verdict=verdict if verdict else 'Unknown',
                    score=score if score is not None else 0,
                    runtime=test_results.get('total_runtime', 0) if test_results else 0,  
                    memory_used=test_results.get('peak_memory', 0),  # Mock memory usage
                    test_cases_passed=test_results.get('passed_count', 0) if test_results else 0,
                    total_test_cases=test_results.get('total_count', 0) if test_results else 0,
                    status='Accepted' if verdict == 'Accepted' else 'Wrong Answer'
                )
                submission_id = submission.id
                print(f"✅ SUCCESS: Created submission with ID: {submission_id}")
                print(f"Submission object: {submission}")
                
            except Exception as e:
                print(f"❌ ERROR creating submission: {type(e).__name__}: {str(e)}")
                print(f"Error details: {e}")
                import traceback
                traceback.print_exc()
                
                # Create a mock ID as fallback
                submission_id = 1
                print("Using mock submission ID: 1")
            
            # Update problem statistics
            try:
                problem.submissions = getattr(problem, 'submissions', 0) + 1
                if verdict == 'Accepted':
                    problem.accepted_submissions = getattr(problem, 'accepted_submissions', 0) + 1
                    problem.acceptance_rate = (problem.accepted_submissions / problem.submissions) * 100
                problem.save()
            except:
                pass  # Skip if fields don't exist
            
            # Format result message
            if verdict == 'Accepted':
                result_message = (
                    "✓ Accepted\n\n"
                    f"{str(test_results['passed_count'])}/{str(test_results['total_count'])} test cases passed.\n"
                    f"Runtime: {test_results['total_runtime']:.2f}ms\n"
                    f"Memory: {test_results['peak_memory']:.2f}\n"
                    f"Score: {score:.1f}/100\n\n"
                    "Congratulations! Your solution has been accepted."
                )
            else:
                failed_test = None
                for result in test_results['results']:
                    if not result['passed']:
                        failed_test = result
                        break
                
                if failed_test and 'error' in failed_test:
                    result_message = (
                        f"✗ {verdict}\n\n"
                        f"Error in Test Case {str(failed_test['test_case'])}:\n"
                        f"{failed_test['error']}\n\n"
                        f"{str(test_results['passed_count'])}/{str(test_results['total_count'])} test cases passed.\n"
                        f"Score: {score:.1f}/100"
                    )
                else:
                    result_message = (
                        f"✗ {verdict}\n\n"
                        f"{str(test_results['passed_count'])}/{str(test_results['total_count'])} test cases passed.\n"
                        f"Runtime: {test_results['total_runtime']:.2f}ms\n"
                        f"Score: {score:.1f}/100\n\n"
                        "First failed test case:\n"
                        f"Input: {str(failed_test['input']) if failed_test else 'N/A'}\n"
                        f"Expected: {str(failed_test['expected']) if failed_test else 'N/A'}\n"
                        f"Your Output: {str(failed_test['actual']) if failed_test else 'N/A'}"
                    )
            
            return JsonResponse({
                'success': True,
                'result': result_message,
                'verdict': verdict,
                'score': score,
                'submission_id': submission_id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)




@login_required
def solution_history(request, user_id, problem_id):
    user = get_object_or_404(User, id=user_id)
    problem = get_object_or_404(Problem, id=problem_id)
    
    # Get all submissions for this user and problem
    submissions = Submission.objects.filter(
        user=user,
        problem=problem
    ).order_by('-submitted_at')
    
    # Calculate statistics
    total_submissions = submissions.count()
    accepted_submissions = submissions.filter(verdict='Accepted').count()
    
    # Check if problem is solved
    is_solved = accepted_submissions > 0
    
    # Get best score and fastest runtime
    best_score = submissions.aggregate(Max('score'))['score__max'] or 0
    fastest_runtime = submissions.filter(
        verdict='Accepted'
    ).aggregate(Min('runtime'))['runtime__min'] or 0
    
    context = {
        'user': user,
        'problem': problem,
        'submissions': submissions,
        'total_submissions': total_submissions,
        'accepted_submissions': accepted_submissions,
        'is_solved': is_solved,
        'best_score': best_score,
        'fastest_runtime': fastest_runtime,
    }
    
    return render(request, 'solution_history_page.html', context)



def monitor_memory_usage(process, memory_tracker):
    """Monitor memory usage of a process in a separate thread"""
    try:
        while process.poll() is None:  # While process is running
            try:
                mem_info = process.memory_info()
                current_memory = mem_info.rss / (1024 * 1024)  # Convert to MB
                memory_tracker['peak'] = max(memory_tracker['peak'], current_memory)
                time.sleep(0.01)  # Check every 10ms
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
    except:
        pass

def get_ai_assistance(request, user_id, problem_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            language = data.get('language', 'python')
            assistance_type = data.get('type', 'hint')  # hint, debug, optimize, explain
            
            problem = get_object_or_404(Problem, id=problem_id)
            
            gemini_service = GeminiService()
            result = gemini_service.get_coding_assistance(
                problem_description=problem.description,
                current_code=code,
                language=language,
                assistance_type=assistance_type
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})