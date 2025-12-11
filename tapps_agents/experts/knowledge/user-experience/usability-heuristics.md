# Nielsen's Usability Heuristics

## Overview

Jakob Nielsen's 10 Usability Heuristics are a set of general principles for interaction design. These heuristics provide a framework for evaluating and improving the usability of user interfaces.

## The 10 Heuristics

### 1. Visibility of System Status
The system should always keep users informed about what is going on, through appropriate feedback within reasonable time.

**Principles:**
- Show current state
- Provide progress indicators
- Loading states
- Status messages
- Clear feedback

**Examples:**
- Progress bars for file uploads
- Loading spinners
- "Saving..." messages
- Breadcrumb navigation
- Active page indicators

**Common Violations:**
- No loading indicators
- Unclear current location
- No status updates
- Silent failures
- Unclear progress

### 2. Match Between System and the Real World
The system should speak the users' language, with words, phrases and concepts familiar to the user, rather than system-oriented terms.

**Principles:**
- Use familiar language
- Follow real-world conventions
- Natural order
- Familiar metaphors
- User terminology

**Examples:**
- "Shopping cart" for e-commerce
- "Trash" or "Recycle bin" for deletion
- Calendar interface
- File folder metaphor
- Natural language forms

**Common Violations:**
- Technical jargon
- System terminology
- Unfamiliar concepts
- Unnatural order
- Confusing labels

### 3. User Control and Freedom
Users often choose system functions by mistake and will need a clearly marked "emergency exit" to leave the unwanted state without having to go through an extended dialogue.

**Principles:**
- Undo functionality
- Cancel buttons
- Escape routes
- Clear exits
- Reversible actions

**Examples:**
- Undo/Redo buttons
- Cancel in dialogs
- Back button
- Close buttons
- Exit without saving

**Common Violations:**
- No undo option
- Trapped in dialogs
- No cancel button
- Irreversible actions
- No escape route

### 4. Consistency and Standards
Users should not have to wonder whether different words, situations, or actions mean the same thing. Follow platform conventions.

**Principles:**
- Consistent terminology
- Standard conventions
- Platform guidelines
- Familiar patterns
- Predictable behavior

**Examples:**
- Consistent button labels
- Standard icons
- Platform conventions
- Consistent navigation
- Familiar patterns

**Common Violations:**
- Inconsistent labels
- Different patterns
- Non-standard conventions
- Unpredictable behavior
- Mixed terminology

### 5. Error Prevention
Even better than good error messages is a careful design which prevents a problem from occurring in the first place.

**Principles:**
- Prevent errors
- Validate input
- Confirm destructive actions
- Provide constraints
- Clear instructions

**Examples:**
- Input validation
- Confirmation dialogs
- Disabled invalid options
- Format hints
- Constraint messages

**Common Violations:**
- No validation
- No confirmations
- Unclear instructions
- Easy to make mistakes
- No prevention

### 6. Recognition Rather Than Recall
Minimize the user's memory load by making objects, actions, and options visible. The user should not have to remember information from one part of the dialogue to another.

**Principles:**
- Show options
- Visible information
- Icons with labels
- Contextual help
- Examples provided

**Examples:**
- Dropdown menus
- Icons with text
- Tooltips
- Contextual help
- Visible history

**Common Violations:**
- Hidden options
- Icons without labels
- No help available
- Must remember information
- Invisible features

### 7. Flexibility and Efficiency of Use
Accelerators — unseen by the novice user — may often speed up the interaction for the expert user such that the system can cater to both inexperienced and experienced users.

**Principles:**
- Keyboard shortcuts
- Customizable interface
- Power user features
- Multiple ways to accomplish tasks
- Efficiency features

**Examples:**
- Keyboard shortcuts
- Customizable toolbars
- Quick actions
- Macros
- Batch operations

**Common Violations:**
- No shortcuts
- No customization
- Only one way to do things
- Slow for experts
- No efficiency features

### 8. Aesthetic and Minimalist Design
Dialogues should not contain information which is irrelevant or rarely needed. Every extra unit of information in a dialogue competes with the relevant units of information and diminishes their relative visibility.

**Principles:**
- Remove clutter
- Focus on essentials
- Clean design
- Clear hierarchy
- Minimal interface

**Examples:**
- Clean layouts
- Focused content
- Progressive disclosure
- Collapsible sections
- Minimal navigation

**Common Violations:**
- Cluttered interface
- Too much information
- Unclear hierarchy
- Distracting elements
- Overwhelming design

### 9. Help Users Recognize, Diagnose, and Recover from Errors
Error messages should be expressed in plain language (no codes), precisely indicate the problem, and constructively suggest a solution.

**Principles:**
- Clear error messages
- Plain language
- Specific problems
- Constructive solutions
- Helpful guidance

**Examples:**
- "Email address is invalid" not "Error 404"
- Specific error descriptions
- Suggested solutions
- Helpful links
- Recovery options

**Common Violations:**
- Technical error codes
- Vague messages
- No solutions
- Unhelpful errors
- Confusing messages

### 10. Help and Documentation
Even though it is better if the system can be used without documentation, it may be necessary to provide help and documentation.

**Principles:**
- Easy to find
- Searchable
- Task-focused
- Clear instructions
- Contextual help

**Examples:**
- Help menus
- Tooltips
- Contextual help
- Video tutorials
- FAQ sections

**Common Violations:**
- Hard to find
- Not searchable
- Unclear instructions
- No help available
- Outdated documentation

## Applying the Heuristics

### Evaluation Process
1. Review each heuristic
2. Identify violations
3. Prioritize issues
4. Suggest improvements
5. Test solutions

### Heuristic Evaluation
- Expert review
- Systematic evaluation
- Document findings
- Rate severity
- Recommend fixes

### Severity Ratings
- **0**: Not a usability problem
- **1**: Cosmetic problem
- **2**: Minor usability problem
- **3**: Major usability problem
- **4**: Usability catastrophe

## Best Practices

### 1. Regular Evaluation
- Conduct heuristic evaluations
- Review against heuristics
- Identify issues early
- Continuous improvement

### 2. Team Training
- Train team on heuristics
- Share knowledge
- Apply consistently
- Reference in reviews

### 3. User Testing
- Combine with user testing
- Validate findings
- Prioritize issues
- Test solutions

### 4. Documentation
- Document violations
- Track improvements
- Share findings
- Maintain records

## Common Patterns

### Error Prevention Pattern
```html
<input type="email" 
       required 
       pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
       aria-invalid="false"
       aria-describedby="email-help">
<span id="email-help">Enter a valid email address</span>
```

### Status Feedback Pattern
```html
<div role="status" aria-live="polite">
  <span class="spinner"></span>
  Saving changes...
</div>
```

### Undo Pattern
```html
<button onclick="undo()" aria-label="Undo last action">
  Undo
</button>
```

## Best Practices Summary

1. **Visibility**: Always show system status
2. **Real World**: Use familiar language
3. **User Control**: Provide undo and escape
4. **Consistency**: Follow standards
5. **Error Prevention**: Prevent mistakes
6. **Recognition**: Show, don't require recall
7. **Flexibility**: Support all user levels
8. **Minimalism**: Remove clutter
9. **Error Recovery**: Helpful error messages
10. **Documentation**: Easy to find help

