from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/api/v1/investigate/domain")
async def investigate_domain():
  return {"message": "Hello World!"}

@app.get("api/v1/investigate/mail")
async def investigate_mail():
  pass

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")