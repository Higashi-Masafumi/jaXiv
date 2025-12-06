from pydantic import BaseModel, HttpUrl


class TranslateResponseSchema(BaseModel):
	message: str
	translated_pdf_url: HttpUrl
	translated_language: str
