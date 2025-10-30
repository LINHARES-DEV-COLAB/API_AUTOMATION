from APP.Interfaces.automation_interface import automation_command


class fidc_command(automation_command):
    def validate_parameters(self, params: dict) -> bool:
        print("🔍 DEBUG COMMAND - validate_parameters chamado")
        return True 
    
    def execute(self, params):
        print("🔍 DEBUG COMMAND - execute chamado")
        from APP.Services.fidc_service import run     
        try:
            print("🔍 DEBUG COMMAND - Antes de chamar run()")
            resultado = run()
            print(f"🔍 DEBUG COMMAND - run() returned: {type(resultado)}")
            
            return {
                "status": "success",
                "data": resultado,
                "automation": "fidc"
            }
        
        except Exception as e:
            print(f"🔍 DEBUG COMMAND - Exception: {e}")
            return {
                "status": "error",
                "message": str(e),
                "automation": "fidc"
            }

