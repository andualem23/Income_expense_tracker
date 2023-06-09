import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from userpreferences.models import UserPreferences

from .models import Catagory, Expense
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
import csv

# Create your views here.

def search_expenses(request):
    if request.method == "POST":
        search_string = json.loads(request.body).get("searchText", "") 


        expenses = Expense.objects.filter(
            amount__istartswith=search_string, owner=request.user) | Expense.objects.filter(
            date__istartswith=search_string, owner=request.user) | Expense.objects.filter(
            description__icontains=search_string, owner=request.user) | Expense.objects.filter(
            catagory__istartswith=search_string, owner=request.user)
            
        data = expenses.values()
        
        return JsonResponse(list(data), safe=False)


@login_required(login_url="/authentication/login")
def index(request):
    expenses = Expense.objects.filter(owner= request.user)
    currency = UserPreferences.objects.get(user=request.user).currency
    paginator = Paginator(expenses, 4)

    page_number= request.GET.get('page')
    
    page_obj = Paginator.get_page(paginator, page_number)
    context = {
        "expenses" :expenses,
        "page_obj": page_obj,
        "currency": currency,
    }

    return render(request, 'expenses/index.html', context)


def add_expense(request):
    catagories = Catagory.objects.all()
    context = {
            "catagories":catagories,
            "values": request.POST
        }
    if request.method == "GET":
        return render(request, 'expenses/add_expense.html' ,context) 

    if request.method == "POST":
        amount = request.POST["amount"]
        description = request.POST["description"]
        catagory = request.POST["catagory"]
        date = request.POST["expense_date"]
        
        if not amount:
            messages.error(request, "Amount is required")
            return render(request, 'expenses/add_expense.html' , context) 
        if not description:
            messages.error(request, "description")
            return render(request, 'expenses/add_expense.html' , context) 

        Expense.objects.create(owner= request.user, amount=amount, description=description, catagory=catagory, date=date)
        messages.success(request, "Expense saved successfully")


        return redirect('expenses')


def edit_expense(request, id):
    expense = Expense.objects.get(pk =id)
    catagories = Catagory.objects.all()

    context = {
            "values": expense,
            "catagories": catagories
        }

    if request.method == "GET":
        
        return render(request, "expenses/edit-expense.html", context)
    else:
        amount = request.POST["amount"]
        description = request.POST["description"]
        catagory = request.POST["catagory"]
        date = request.POST["expense_date"]
        
        if not amount:
            messages.error(request, "Amount is required")
            return render(request, 'expenses/edit_expense.html' , context) 
        if not description:
            messages.error(request, "description")
            return render(request, 'expenses/edit_expense.html' , context) 

        expense.amount = amount
        expense.date = date
        expense.catagory = catagory
        expense.description = description

        expense.save()

        messages.success(request, "Expense Updated successfully")

        return render(request, "expenses/edit-expense.html", context)


def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, "Expenses Deleted Successfully")
    return redirect("expenses")


def expense_catagory_summary(request):
    today = datetime.date.today()
    six_month_ago = today-datetime.timedelta(days=30*6)

    expenses = Expense.objects.filter(date__gte=six_month_ago, date__lte=today, owner=request.user)

    catagories = Catagory.objects.all()
    expense_catagory_data = {}
    for catagory in catagories:
        expense_catagory_data[catagory.name] = 0

        for expense in expenses:
            if expense.catagory == catagory.name:
                expense_catagory_data[catagory.name] += expense.amount

    return JsonResponse({"expense_catagory_data": expense_catagory_data }, safe=False)
    

def  stats(request):
    return render(request, "expenses/stats.html")
        

def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] ="attachment; filename=Expenses" + str(datetime.datetime.now()) + ".csv"

    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Catagory', 'Date'])

    expenses = Expense.objects.filter(owner = request.user)

    for expense in expenses:
        writer.writerow([expense.amount, expense.description, expense.catagory, expense.date])

    return response
