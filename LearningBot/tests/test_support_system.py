"""
Comprehensive tests for support system functionality
"""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from services.support import SupportService
from services.notification import NotificationService
from database.models import SupportTicket, SupportResponse, User, Admin


class TestSupportService:
    """Test SupportService functionality"""
    
    @pytest.mark.asyncio
    async def test_create_support_ticket(self, db_session, sample_user):
        """Test creating a new support ticket"""
        support_service = SupportService(db_session)
        
        message = "I can't access my purchased lesson"
        
        ticket = await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message=message,
            priority="normal"
        )
        
        assert ticket is not None
        assert ticket.initial_message == message
        assert ticket.status == "open"
        assert ticket.priority == "normal"
        assert ticket.ticket_number.startswith("TK")
        assert len(ticket.ticket_number) == 8  # TK + 6 chars
        assert ticket.user_id == sample_user.user_id
    
    @pytest.mark.asyncio
    async def test_get_user_tickets(self, db_session, sample_user):
        """Test retrieving tickets for a specific user"""
        support_service = SupportService(db_session)
        
        # Create multiple tickets
        await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="First issue",
            priority="normal"
        )
        await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="Second issue",
            priority="high"
        )
        
        tickets = await support_service.get_user_tickets(sample_user.user_id)
        
        assert len(tickets) == 2
        assert all(ticket.user_id == sample_user.user_id for ticket in tickets)
        # Should be ordered by creation date desc
        assert tickets[0].created_at >= tickets[1].created_at
    
    @pytest.mark.asyncio
    async def test_get_admin_tickets(self, db_session, sample_user, sample_admin):
        """Test retrieving tickets for admin interface"""
        support_service = SupportService(db_session)
        
        # Create tickets with different statuses
        await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="Open ticket",
            priority="normal"
        )
        
        ticket2 = await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="In progress ticket",
            priority="high"
        )
        await support_service.update_ticket_status(ticket2.id, "in_progress", sample_admin.user_id)
        
        # Get all tickets
        all_tickets = await support_service.get_admin_tickets()
        assert len(all_tickets) == 2
        
        # Get only open tickets
        open_tickets = await support_service.get_tickets_by_status("open")
        assert len(open_tickets) == 1
        assert open_tickets[0].status == "open"
        
        # Get in_progress tickets
        in_progress_tickets = await support_service.get_tickets_by_status("in_progress")
        assert len(in_progress_tickets) == 1
        assert in_progress_tickets[0].status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_add_response_to_ticket(self, db_session, sample_user, sample_admin):
        """Test adding responses to tickets"""
        support_service = SupportService(db_session)
        
        # Create a ticket
        ticket = await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="I need help",
            priority="normal"
        )
        
        # Add admin response
        admin_response = await support_service.add_response(
            ticket_id=ticket.id,
            sender_id=sample_admin.user_id,
            message="How can I help you?",
            sender_type="admin"
        )
        
        assert admin_response is not None
        assert admin_response.message == "How can I help you?"
        assert admin_response.sender_type == "admin"
        assert admin_response.sender_id == sample_admin.user_id
        assert not admin_response.is_internal
        
        # Add user response
        user_response = await support_service.add_response(
            ticket_id=ticket.id,
            sender_id=sample_user.user_id,
            message="Thanks! I can't find my lesson.",
            sender_type="user"
        )
        
        assert user_response is not None
        assert user_response.sender_type == "user"
        
        # Get ticket with responses
        updated_ticket = await support_service.get_ticket_by_id(ticket.id)
        assert len(updated_ticket.responses) == 2
    
    @pytest.mark.asyncio
    async def test_update_ticket_status(self, db_session, sample_user, sample_admin):
        """Test updating ticket status and assignment"""
        support_service = SupportService(db_session)
        
        # Create a ticket
        ticket = await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="Test issue",
            priority="normal"
        )
        
        # Assign to admin and set to in_progress
        success = await support_service.update_ticket_status(
            ticket_id=ticket.id,
            status="in_progress",
            admin_id=sample_admin.user_id
        )
        
        assert success
        
        # Verify the update
        updated_ticket = await support_service.get_ticket_by_id(ticket.id)
        assert updated_ticket.status == "in_progress"
        assert updated_ticket.assigned_admin_id == sample_admin.user_id
        
        # Close the ticket
        success = await support_service.close_ticket(ticket.id, sample_admin.user_id)
        assert success
        
        closed_ticket = await support_service.get_ticket_by_id(ticket.id)
        assert closed_ticket.status == "closed"
        assert closed_ticket.closed_at is not None
    
    @pytest.mark.asyncio
    async def test_ticket_number_uniqueness(self, db_session, sample_user):
        """Test that ticket numbers are unique"""
        support_service = SupportService(db_session)
        
        # Create multiple tickets
        tickets = []
        for i in range(5):
            ticket = await support_service.create_support_ticket(
                user_id=sample_user.user_id,
                message=f"Issue {i}",
                priority="normal"
            )
            tickets.append(ticket)
        
        # Check all ticket numbers are unique
        ticket_numbers = [t.ticket_number for t in tickets]
        assert len(set(ticket_numbers)) == len(ticket_numbers)


class TestNotificationService:
    """Test NotificationService functionality"""
    
    @pytest.mark.asyncio
    async def test_notify_admins_of_support_request(self, db_session, sample_user, sample_admin):
        """Test admin notification for new support requests"""
        mock_bot = AsyncMock()
        notification_service = NotificationService(mock_bot, db_session)
        
        # Create a ticket
        support_service = SupportService(db_session)
        ticket = await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="I need urgent help",
            priority="urgent"
        )
        
        # Mock admin service to return our test admin
        with patch.object(notification_service, 'admin_service') as mock_admin_service:
            mock_admin_service.get_all_admins.return_value = [sample_admin]
            
            # Call notification
            result = await notification_service.notify_admins_of_support_request(ticket)
            
            assert result is True
            mock_bot.send_message.assert_called_once()
            
            # Check the message content
            call_args = mock_bot.send_message.call_args
            assert call_args[1]['chat_id'] == sample_admin.user_id
            assert ticket.ticket_number in call_args[1]['text']
            assert "urgent" in call_args[1]['text'].lower()
    
    @pytest.mark.asyncio
    async def test_notify_user_of_response(self, db_session, sample_user):
        """Test user notification for support responses"""
        mock_bot = AsyncMock()
        notification_service = NotificationService(mock_bot, db_session)
        
        # Create a mock ticket
        ticket = Mock()
        ticket.ticket_number = "TK123456"
        ticket.user_id = sample_user.user_id
        
        # Send notification
        result = await notification_service.notify_user_of_response(
            ticket=ticket,
            response_message="We'll help you right away!",
            admin_name="Support Team"
        )
        
        assert result is True
        mock_bot.send_message.assert_called_once()
        
        # Check the message
        call_args = mock_bot.send_message.call_args
        assert call_args[1]['chat_id'] == sample_user.user_id
        assert ticket.ticket_number in call_args[1]['text']
        assert "We'll help you right away!" in call_args[1]['text']


class TestSupportHandlers:
    """Test support handlers functionality"""
    
    @pytest.mark.asyncio
    async def test_show_support_handler(self, db_session):
        """Test show_support callback handler"""
        from handlers.user.start import show_support
        
        # Mock callback and state
        callback = Mock()
        callback.from_user.id = 12345
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        state = AsyncMock()
        
        # Mock user service
        with patch('handlers.user.start.UserService') as mock_user_service:
            mock_service_instance = AsyncMock()
            mock_user_service.return_value = mock_service_instance
            
            # Call handler
            await show_support(callback, db_session, state)
            
            # Verify state was set
            state.set_state.assert_called_once()
            
            # Verify message was sent
            callback.message.edit_text.assert_called_once()
            callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_support_message_creates_ticket(self, db_session, sample_user):
        """Test that handling support message creates a ticket"""
        from handlers.user.start import handle_support_message
        
        # Mock message
        message = Mock()
        message.from_user.id = sample_user.user_id
        message.text = "I need help with my account"
        message.answer = AsyncMock()
        
        # Mock bot
        mock_bot = AsyncMock()
        
        state = AsyncMock()
        
        # Call handler
        await handle_support_message(message, db_session, state, mock_bot)
        
        # Verify ticket was created
        support_service = SupportService(db_session)
        tickets = await support_service.get_user_tickets(sample_user.user_id)
        
        assert len(tickets) == 1
        assert tickets[0].initial_message == "I need help with my account"
        
        # Verify user received confirmation
        message.answer.assert_called_once()
        
        # Verify state was cleared
        state.clear.assert_called_once()


class TestSupportModels:
    """Test support database models"""
    
    @pytest.mark.asyncio
    async def test_support_ticket_model(self, db_session, sample_user):
        """Test SupportTicket model creation and relationships"""
        # Create ticket directly
        ticket = SupportTicket(
            user_id=sample_user.user_id,
            ticket_number="TK123456",
            subject="Test Issue",
            initial_message="This is a test",
            status="open",
            priority="normal",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db_session.add(ticket)
        await db_session.commit()
        await db_session.refresh(ticket)
        
        assert ticket.id is not None
        assert ticket.user_id == sample_user.user_id
        assert ticket.status == "open"
        assert ticket.priority == "normal"
    
    @pytest.mark.asyncio
    async def test_support_response_model(self, db_session, sample_user):
        """Test SupportResponse model creation"""
        # Create ticket first
        ticket = SupportTicket(
            user_id=sample_user.user_id,
            ticket_number="TK123456",
            subject="Test Issue",
            initial_message="This is a test",
            status="open",
            priority="normal",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db_session.add(ticket)
        await db_session.commit()
        await db_session.refresh(ticket)
        
        # Create response
        response = SupportResponse(
            ticket_id=ticket.id,
            sender_type="admin",
            sender_id=99999,
            message="How can I help you?",
            is_internal=False,
            created_at=datetime.now(timezone.utc)
        )
        
        db_session.add(response)
        await db_session.commit()
        await db_session.refresh(response)
        
        assert response.id is not None
        assert response.ticket_id == ticket.id
        assert response.sender_type == "admin"
        assert response.message == "How can I help you?"


class TestEndToEndSupportFlow:
    """Test complete support flow end-to-end"""
    
    @pytest.mark.asyncio
    async def test_complete_support_workflow(self, db_session, sample_user, sample_admin):
        """Test complete support workflow from user request to admin response"""
        
        # Step 1: User creates support request
        support_service = SupportService(db_session)
        mock_bot = AsyncMock()
        notification_service = NotificationService(mock_bot, db_session)
        
        # Create ticket
        ticket = await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message="I can't access my premium lesson",
            priority="normal"
        )
        
        assert ticket is not None
        assert ticket.status == "open"
        
        # Step 2: Notify admins (mock the admin service call)
        with patch.object(notification_service, 'admin_service') as mock_admin_service:
            mock_admin_service.get_all_admins.return_value = [sample_admin]
            
            notification_sent = await notification_service.notify_admins_of_support_request(ticket)
            assert notification_sent is True
        
        # Step 3: Admin takes ticket and responds
        assigned = await support_service.assign_ticket(ticket.id, sample_admin.user_id)
        assert assigned is True
        
        # Verify status changed
        updated_ticket = await support_service.get_ticket_by_id(ticket.id)
        assert updated_ticket.status == "in_progress"
        assert updated_ticket.assigned_admin_id == sample_admin.user_id
        
        # Admin adds response
        admin_response = await support_service.add_response(
            ticket_id=ticket.id,
            sender_id=sample_admin.user_id,
            message="I've checked your account. The lesson should be accessible now.",
            sender_type="admin"
        )
        
        assert admin_response is not None
        
        # Step 4: User responds back
        user_response = await support_service.add_response(
            ticket_id=ticket.id,
            sender_id=sample_user.user_id,
            message="Thank you! It's working now.",
            sender_type="user"
        )
        
        assert user_response is not None
        
        # Step 5: Admin closes ticket
        closed = await support_service.close_ticket(ticket.id, sample_admin.user_id)
        assert closed is True
        
        # Verify final state
        final_ticket = await support_service.get_ticket_by_id(ticket.id)
        assert final_ticket.status == "closed"
        assert final_ticket.closed_at is not None
        assert len(final_ticket.responses) == 2
        
        # Verify response order and content
        responses = sorted(final_ticket.responses, key=lambda r: r.created_at)
        assert responses[0].sender_type == "admin"
        assert responses[1].sender_type == "user"
        assert "accessible now" in responses[0].message
        assert "working now" in responses[1].message
    
    @pytest.mark.asyncio
    async def test_multiple_tickets_management(self, db_session, sample_user, sample_admin):
        """Test managing multiple tickets with different statuses"""
        support_service = SupportService(db_session)
        
        # Create multiple tickets
        tickets = []
        for i in range(3):
            ticket = await support_service.create_support_ticket(
                user_id=sample_user.user_id,
                message=f"Issue number {i+1}",
                priority="normal" if i % 2 == 0 else "high"
            )
            tickets.append(ticket)
        
        # Assign different statuses
        await support_service.assign_ticket(tickets[0].id, sample_admin.user_id)  # in_progress
        await support_service.close_ticket(tickets[1].id, sample_admin.user_id)   # closed
        # tickets[2] remains open
        
        # Test filtering
        open_tickets = await support_service.get_tickets_by_status("open")
        in_progress_tickets = await support_service.get_tickets_by_status("in_progress")
        closed_tickets = await support_service.get_tickets_by_status("closed")
        
        assert len(open_tickets) == 1
        assert len(in_progress_tickets) == 1
        assert len(closed_tickets) == 1
        
        # Test admin view
        admin_tickets = await support_service.get_admin_tickets()
        assert len(admin_tickets) == 3
        
        # Test user view
        user_tickets = await support_service.get_user_tickets(sample_user.user_id)
        assert len(user_tickets) == 3


@pytest.mark.asyncio
async def test_support_system_performance(db_session, sample_user):
    """Test support system performance with many tickets"""
    support_service = SupportService(db_session)
    
    # Create many tickets
    start_time = datetime.now()
    
    for i in range(50):
        await support_service.create_support_ticket(
            user_id=sample_user.user_id,
            message=f"Performance test issue {i}",
            priority="normal"
        )
    
    creation_time = (datetime.now() - start_time).total_seconds()
    
    # Should create 50 tickets in reasonable time (< 5 seconds)
    assert creation_time < 5.0
    
    # Test retrieval performance
    start_time = datetime.now()
    tickets = await support_service.get_user_tickets(sample_user.user_id, limit=50)
    retrieval_time = (datetime.now() - start_time).total_seconds()
    
    assert len(tickets) == 50
    assert retrieval_time < 1.0  # Should retrieve quickly