"""
Message Queue System for PyCraft 2D Multiplayer

Provides priority-based message queuing, batching, and performance optimization
for efficient message broadcasting.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import heapq

from ..message_types import MessageType


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 0    # Connection events, errors
    HIGH = 1        # Player death, important game events
    NORMAL = 2      # Regular position updates, actions
    LOW = 3         # Cosmetic effects, non-essential updates
    BULK = 4        # Large data transfers, chunk data


@dataclass
class QueuedMessage:
    """A message in the queue with metadata."""
    priority: MessagePriority
    message_type: MessageType
    data: Dict[str, Any]
    targets: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    sender_id: Optional[str] = None
    reliable: bool = False
    attempts: int = 0
    max_attempts: int = 3
    
    def __lt__(self, other):
        """Enable priority queue ordering."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp


class MessageBatch:
    """A batch of messages for efficient processing."""
    
    def __init__(self, max_size: int = 10, max_bytes: int = 8192):
        """
        Initialize message batch.
        
        Args:
            max_size: Maximum number of messages in batch
            max_bytes: Maximum bytes in batch
        """
        self.max_size = max_size
        self.max_bytes = max_bytes
        self.messages: List[QueuedMessage] = []
        self.total_bytes = 0
        self.created_time = time.time()
    
    def can_add(self, message: QueuedMessage) -> bool:
        """Check if message can be added to batch."""
        if len(self.messages) >= self.max_size:
            return False
        
        # Estimate message size
        message_size = len(str(message.data))
        if self.total_bytes + message_size > self.max_bytes:
            return False
        
        return True
    
    def add_message(self, message: QueuedMessage) -> bool:
        """
        Add message to batch.
        
        Returns:
            True if message was added
        """
        if not self.can_add(message):
            return False
        
        self.messages.append(message)
        self.total_bytes += len(str(message.data))
        return True
    
    def is_ready(self, max_age: float = 0.1) -> bool:
        """Check if batch is ready for processing."""
        # Ready if full
        if len(self.messages) >= self.max_size:
            return True
        
        # Ready if too old
        if time.time() - self.created_time > max_age:
            return True
        
        # Ready if has critical messages
        return any(msg.priority == MessagePriority.CRITICAL for msg in self.messages)
    
    def get_messages(self) -> List[QueuedMessage]:
        """Get all messages in batch."""
        return self.messages.copy()
    
    def clear(self):
        """Clear the batch."""
        self.messages.clear()
        self.total_bytes = 0
        self.created_time = time.time()


class MessageQueue:
    """
    Priority-based message queue with batching and throttling.
    
    Manages message ordering, batching, and flow control for optimal performance.
    """
    
    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize message queue.
        
        Args:
            max_queue_size: Maximum number of queued messages
        """
        self.max_queue_size = max_queue_size
        
        # Priority queues for different message types
        self.priority_queues: Dict[MessagePriority, List[QueuedMessage]] = {
            priority: [] for priority in MessagePriority
        }
        
        # Message batching
        self.current_batch: Optional[MessageBatch] = None
        self.batch_max_size = 10
        self.batch_max_age = 0.05  # 50ms
        
        # Throttling
        self.throttle_limits: Dict[MessagePriority, float] = {
            MessagePriority.CRITICAL: float('inf'),  # No throttling
            MessagePriority.HIGH: 100.0,             # 100 msgs/sec
            MessagePriority.NORMAL: 50.0,            # 50 msgs/sec
            MessagePriority.LOW: 20.0,               # 20 msgs/sec
            MessagePriority.BULK: 5.0                # 5 msgs/sec
        }
        
        self.throttle_timestamps: Dict[MessagePriority, deque] = {
            priority: deque() for priority in MessagePriority
        }
        
        # Threading
        self.queue_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'messages_queued': 0,
            'messages_processed': 0,
            'messages_dropped': 0,
            'messages_throttled': 0,
            'batches_created': 0,
            'queue_size': 0
        }
    
    def enqueue(self, message: QueuedMessage) -> bool:
        """
        Add message to queue.
        
        Args:
            message: Message to queue
            
        Returns:
            True if message was queued successfully
        """
        with self.queue_lock:
            # Check queue size limit
            total_queued = sum(len(queue) for queue in self.priority_queues.values())
            if total_queued >= self.max_queue_size:
                self.stats['messages_dropped'] += 1
                return False
            
            # Check throttling
            if not self._check_throttle(message.priority):
                self.stats['messages_throttled'] += 1
                return False
            
            # Add to appropriate priority queue
            heapq.heappush(self.priority_queues[message.priority], message)
            self.stats['messages_queued'] += 1
            self.stats['queue_size'] = total_queued + 1
            
            return True
    
    def dequeue_batch(self) -> Optional[MessageBatch]:
        """
        Get next batch of messages for processing.
        
        Returns:
            Batch of messages or None if no messages ready
        """
        with self.queue_lock:
            # Create new batch if needed
            if self.current_batch is None:
                self.current_batch = MessageBatch(self.batch_max_size)
            
            # Fill batch with messages by priority
            for priority in MessagePriority:
                queue = self.priority_queues[priority]
                
                while queue and self.current_batch.can_add(queue[0]):
                    message = heapq.heappop(queue)
                    self.current_batch.add_message(message)
                    self.stats['messages_processed'] += 1
                    
                    # Critical messages create immediate batch
                    if message.priority == MessagePriority.CRITICAL:
                        break
            
            # Return batch if ready
            if self.current_batch.is_ready(self.batch_max_age):
                batch = self.current_batch
                self.current_batch = None
                self.stats['batches_created'] += 1
                return batch
            
            return None
    
    def dequeue_single(self, priority: Optional[MessagePriority] = None) -> Optional[QueuedMessage]:
        """
        Get single highest priority message.
        
        Args:
            priority: Specific priority to dequeue, or None for highest
            
        Returns:
            Highest priority message or None
        """
        with self.queue_lock:
            if priority:
                # Dequeue from specific priority
                queue = self.priority_queues[priority]
                if queue:
                    message = heapq.heappop(queue)
                    self.stats['messages_processed'] += 1
                    return message
            else:
                # Dequeue highest priority message
                for priority in MessagePriority:
                    queue = self.priority_queues[priority]
                    if queue:
                        message = heapq.heappop(queue)
                        self.stats['messages_processed'] += 1
                        return message
            
            return None
    
    def peek(self, priority: Optional[MessagePriority] = None) -> Optional[QueuedMessage]:
        """
        Look at next message without removing it.
        
        Args:
            priority: Specific priority to peek, or None for highest
            
        Returns:
            Next message or None
        """
        with self.queue_lock:
            if priority:
                queue = self.priority_queues[priority]
                return queue[0] if queue else None
            else:
                for priority in MessagePriority:
                    queue = self.priority_queues[priority]
                    if queue:
                        return queue[0]
            
            return None
    
    def size(self, priority: Optional[MessagePriority] = None) -> int:
        """
        Get queue size.
        
        Args:
            priority: Specific priority or None for total
            
        Returns:
            Number of queued messages
        """
        with self.queue_lock:
            if priority:
                return len(self.priority_queues[priority])
            else:
                return sum(len(queue) for queue in self.priority_queues.values())
    
    def clear(self, priority: Optional[MessagePriority] = None):
        """
        Clear queue.
        
        Args:
            priority: Specific priority to clear, or None for all
        """
        with self.queue_lock:
            if priority:
                self.priority_queues[priority].clear()
            else:
                for queue in self.priority_queues.values():
                    queue.clear()
                self.current_batch = None
    
    def set_throttle_limit(self, priority: MessagePriority, messages_per_second: float):
        """
        Set throttling limit for priority level.
        
        Args:
            priority: Message priority
            messages_per_second: Maximum messages per second
        """
        self.throttle_limits[priority] = messages_per_second
    
    def _check_throttle(self, priority: MessagePriority) -> bool:
        """Check if message passes throttling limits."""
        limit = self.throttle_limits[priority]
        if limit == float('inf'):
            return True
        
        current_time = time.time()
        timestamps = self.throttle_timestamps[priority]
        
        # Remove old timestamps (older than 1 second)
        while timestamps and current_time - timestamps[0] > 1.0:
            timestamps.popleft()
        
        # Check if under limit
        if len(timestamps) < limit:
            timestamps.append(current_time)
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self.queue_lock:
            queue_sizes = {
                priority.name: len(queue) 
                for priority, queue in self.priority_queues.items()
            }
            
            return {
                **self.stats,
                'queue_sizes_by_priority': queue_sizes,
                'current_batch_size': len(self.current_batch.messages) if self.current_batch else 0,
                'throttle_limits': {p.name: limit for p, limit in self.throttle_limits.items()}
            }
    
    def reset_statistics(self):
        """Reset queue statistics."""
        self.stats = {
            'messages_queued': 0,
            'messages_processed': 0,
            'messages_dropped': 0,
            'messages_throttled': 0,
            'batches_created': 0,
            'queue_size': 0
        }


class PriorityMessageQueue:
    """
    Simplified priority queue for immediate processing.
    
    For use cases where batching is not needed and messages
    should be processed immediately in priority order.
    """
    
    def __init__(self):
        """Initialize priority message queue."""
        self.queues: Dict[MessagePriority, deque] = {
            priority: deque() for priority in MessagePriority
        }
        self.queue_lock = threading.Lock()
        self.total_size = 0
    
    def put(self, message: QueuedMessage):
        """Add message to queue."""
        with self.queue_lock:
            self.queues[message.priority].append(message)
            self.total_size += 1
    
    def get(self) -> Optional[QueuedMessage]:
        """Get highest priority message."""
        with self.queue_lock:
            # Check queues in priority order
            for priority in MessagePriority:
                queue = self.queues[priority]
                if queue:
                    self.total_size -= 1
                    return queue.popleft()
            
            return None
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self.total_size == 0
    
    def qsize(self) -> int:
        """Get total queue size."""
        return self.total_size
    
    def clear(self):
        """Clear all queues."""
        with self.queue_lock:
            for queue in self.queues.values():
                queue.clear()
            self.total_size = 0


class MessageScheduler:
    """
    Advanced message scheduler with timing and dependency management.
    
    Allows scheduling messages for future delivery and managing
    message dependencies and ordering constraints.
    """
    
    def __init__(self):
        """Initialize message scheduler."""
        self.scheduled_messages: List[tuple] = []  # (timestamp, message)
        self.dependencies: Dict[str, List[str]] = {}  # message_id -> dependent_ids
        self.completed_messages: Set[str] = set()
        self.scheduler_lock = threading.Lock()
    
    def schedule_message(self, message: QueuedMessage, delay: float) -> str:
        """
        Schedule message for future delivery.
        
        Args:
            message: Message to schedule
            delay: Delay in seconds
            
        Returns:
            Message ID for tracking
        """
        deliver_time = time.time() + delay
        message_id = f"scheduled_{time.time()}_{id(message)}"
        
        with self.scheduler_lock:
            heapq.heappush(self.scheduled_messages, (deliver_time, message_id, message))
        
        return message_id
    
    def add_dependency(self, message_id: str, depends_on: str):
        """
        Add dependency between messages.
        
        Args:
            message_id: ID of message that depends
            depends_on: ID of message it depends on
        """
        with self.scheduler_lock:
            if message_id not in self.dependencies:
                self.dependencies[message_id] = []
            self.dependencies[message_id].append(depends_on)
    
    def mark_completed(self, message_id: str):
        """Mark message as completed."""
        with self.scheduler_lock:
            self.completed_messages.add(message_id)
    
    def get_ready_messages(self) -> List[QueuedMessage]:
        """Get messages ready for delivery."""
        current_time = time.time()
        ready_messages = []
        
        with self.scheduler_lock:
            # Get messages whose time has come
            while (self.scheduled_messages and 
                   self.scheduled_messages[0][0] <= current_time):
                
                deliver_time, message_id, message = heapq.heappop(self.scheduled_messages)
                
                # Check dependencies
                dependencies = self.dependencies.get(message_id, [])
                if all(dep_id in self.completed_messages for dep_id in dependencies):
                    ready_messages.append(message)
                    self.mark_completed(message_id)
                else:
                    # Reschedule for later
                    heapq.heappush(self.scheduled_messages, 
                                 (current_time + 0.1, message_id, message))
        
        return ready_messages
    
    def clear_completed(self):
        """Clear completed message tracking."""
        with self.scheduler_lock:
            self.completed_messages.clear()
