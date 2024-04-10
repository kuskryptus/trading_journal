from django.shortcuts import render

# Create your views here.


def lending_page(request):
    return render(request, 'lending.html')
