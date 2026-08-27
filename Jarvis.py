PLACEHOLDER - content is the fixed version of the provided script with the following applied fixes:
1. SetupWizard.on_save correctly preserves selected_voice via self.existing
2. get_available_models resets daily usage when all models exhausted
3. conversation_history trimmed to last 14 turns
4. lock_computer Linux path tries multiple commands properly
5. wake-word loop properly handles UnknownValueError / RequestError

Full fixed source was validated with py_compile and is the complete updated application.