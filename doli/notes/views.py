from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.views.generic.create_update import update_object
from django.views.generic.create_update import delete_object
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
 
from models import Notes
from forms import CreateNoteForm
from django.shortcuts import render
from django.http import HttpResponseRedirect

@login_required 
def notes_list(request):
    """Show all notes"""
 
    return object_list(request, 
        queryset=Notes.objects.filter(user=request.user),
        template_name='notes/list.html',
        template_object_name='note'
    )

@login_required
def notes_detail(request, id):
    """View note detail based on note id"""
 
    return object_detail(request,
        queryset=Notes.objects.filter(user=request.user),
        object_id=id,
        template_name='notes/detail.html',
        template_object_name='note'
    )

@login_required
def notes_create(request):
    """Create new noew"""

    form = CreateNoteForm(request.POST or None)
    if form.is_valid():
        title = form.cleaned_data['title']
        content = form.cleaned_data['content']
        Notes.objects.create(user_id=request.user.id, title=title, content=content)
        return HttpResponseRedirect(reverse('notes_list'))
    return render(request, 'notes/create.html', {'form': form}) 
    #return create_object(request,
    #     form_class=CreateNoteForm,
    #    template_name='notes/create.html',
    #    post_save_redirect=reverse("notes_list")
    #)            

@login_required
def notes_update(request, id):
    """Update note based on id"""
 
    return update_object(request,
        model=Notes,
        object_id=id,
        template_name='notes/update.html',
        post_save_redirect=reverse("notes_list")
    )            

@login_required
def notes_delete(request, id):
    """Delete a note based on id"""
 
    return delete_object(request,
        model=Notes,
        object_id=id,
        template_name='notes/delete.html',
        post_delete_redirect=reverse("notes_list")
    )
