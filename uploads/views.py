from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from services.upload_service import UploadService, UploadError
from .models import UploadedDocument
from uploads.forms import DocumentUploadForm


# Initialize service
upload_service = UploadService()


@login_required
@require_http_methods(["GET", "POST"])
def document_upload_view(request):
    """
    View for uploading PDF and DOCX documents.
    Handles both GET (display form) and POST (process upload) requests.
    Requirements: 3.4
    """
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        
        if not form.is_valid():
            # Display field-specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'uploads/upload_form.html', {'form': form})
        
        try:
            # Get teacher ID from logged-in user
            teacher = request.user.teacher_profile
            
            # Get validated file
            uploaded_file = form.cleaned_data['document']
            
            # Save uploaded file
            document = upload_service.save_uploaded_file(uploaded_file, teacher.pk)
            
            messages.success(
                request,
                f'Document "{uploaded_file.name}" uploaded successfully. Status: {document.processing_status}'
            )
            return redirect('uploads:document_list')
            
        except AttributeError:
            messages.error(request, 'Only teachers can upload documents.')
            return redirect('users:teacher_login')
            
        except UploadError as e:
            messages.error(request, f'Upload failed: {str(e)}')
            return render(request, 'uploads/upload_form.html', {'form': form})
            
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
            return render(request, 'uploads/upload_form.html', {'form': form})
    
    # GET request - display upload form
    form = DocumentUploadForm()
    return render(request, 'uploads/upload_form.html', {'form': form})


@login_required
@require_http_methods(["GET"])
def document_list_view(request):
    """
    View for displaying list of uploaded documents.
    Shows all documents uploaded by the logged-in teacher.
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    try:
        # Get teacher ID from logged-in user
        teacher = request.user.teacher_profile
        
        # Get all documents uploaded by this teacher
        documents = upload_service.get_teacher_documents(teacher.pk)
        
        # Add pagination
        paginator = Paginator(documents, 20)  # 20 documents per page
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        context = {
            'page_obj': page_obj,
            'total_count': paginator.count,
        }
        
        return render(request, 'uploads/document_list.html', context)
        
    except AttributeError:
        messages.error(request, 'Only teachers can view uploaded documents.')
        return redirect('users:teacher_login')


@login_required
@require_http_methods(["POST"])
def document_delete_view(request, document_id):
    """
    View for deleting an uploaded document.
    Only the teacher who uploaded the document can delete it.
    """
    try:
        # Get teacher ID from logged-in user
        teacher = request.user.teacher_profile
        
        # Get document
        document = upload_service.get_document_by_id(document_id)
        
        if not document:
            messages.error(request, 'Document not found.')
            return redirect('uploads:document_list')
        
        # Check if teacher owns this document
        if document.uploaded_by_id != teacher.pk:
            messages.error(request, 'You can only delete your own documents.')
            return redirect('uploads:document_list')
        
        # Delete document
        file_name = document.file_path
        if upload_service.delete_document(document_id):
            messages.success(request, f'Document "{file_name}" deleted successfully.')
        else:
            messages.error(request, 'Failed to delete document.')
        
        return redirect('uploads:document_list')
        
    except AttributeError:
        messages.error(request, 'Only teachers can delete documents.')
        return redirect('users:teacher_login')



@login_required
@require_http_methods(["GET", "POST"])
def document_process_view(request, document_id):
    """
    View for processing a document (text extraction only).
    Handles both GET (display confirmation) and POST (trigger processing) requests.
    """
    from services.document_processing_service import DocumentProcessingService, DocumentProcessingError
    
    processing_service = DocumentProcessingService()
    
    try:
        # Get teacher ID from logged-in user
        teacher = request.user.teacher_profile
        
        # Get document
        document = upload_service.get_document_by_id(document_id)
        
        if not document:
            messages.error(request, 'Document not found.')
            return redirect('uploads:document_list')
        
        # Check if teacher owns this document
        if document.uploaded_by_id != teacher.pk:
            messages.error(request, 'You can only process your own documents.')
            return redirect('uploads:document_list')
        
        if request.method == 'POST':
            try:
                # Process document (text extraction only)
                extracted_content = processing_service.process_document(document_id)
                
                messages.success(
                    request,
                    f'Document processed successfully. '
                    f'Extracted {len(extracted_content.raw_text)} characters of text.'
                )
                
                # Redirect to document list
                return redirect('uploads:document_list')
                
            except DocumentProcessingError as e:
                messages.error(request, f'Processing failed: {str(e)}')
                return redirect('uploads:document_list')
        
        # GET request - display processing confirmation
        context = {
            'document': document
        }
        return render(request, 'uploads/process_confirm.html', context)
        
    except AttributeError:
        messages.error(request, 'Only teachers can process documents.')
        return redirect('users:teacher_login')








