"""Servidor HTTP para controle remoto do Blender via Express'Arte Studio.
Este script deve ser executado DENTRO do Blender (Text Editor > Run Script)
ou como um addon. Ele expõe uma API local na porta 8090.
"""
import bpy
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class BlenderAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "online", "blender_version": bpy.app.version_string}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/blender/command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('command')
                params = data.get('params', {})
                
                result = execute_blender_command(command, params)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def execute_blender_command(command, params):
    """Executa comandos básicos de modelagem no Blender."""
    if command == 'create_keychain':
        # Cria um torus simples como base de chaveiro
        bpy.ops.mesh.primitive_torus_add(
            align='WORLD', 
            location=(0, 0, 0), 
            major_radius=0.02, 
            minor_radius=0.005
        )
        obj = bpy.context.active_object
        obj.name = params.get('name', 'Keychain')
        return {"success": True, "object": obj.name}
    
    elif command == 'create_character':
        # Cria um cubo como placeholder de personagem
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
        obj = bpy.context.active_object
        obj.name = params.get('name', 'Character')
        return {"success": True, "object": obj.name}
        
    elif command == 'edit_object':
        obj_name = params.get('obj_name')
        operation = params.get('operation')
        obj = bpy.data.objects.get(obj_name)
        if obj:
            if operation == 'scale':
                factor = params.get('factor', 1.0)
                obj.scale = (factor, factor, factor)
            elif operation == 'move':
                loc = params.get('location', [0,0,0])
                obj.location = loc
            return {"success": True, "message": f"Objeto {obj_name} editado."}
        else:
            return {"error": f"Objeto {obj_name} não encontrado."}
            
    return {"error": f"Comando desconhecido: {command}"}

def run_server():
    server = HTTPServer(('127.0.0.1', 8090), BlenderAPIHandler)
    print("Servidor Blender API rodando em http://127.0.0.1:8090")
    server.serve_forever()

# Inicia o servidor em uma thread separada para não travar a UI do Blender
thread = threading.Thread(target=run_server, daemon=True)
thread.start()