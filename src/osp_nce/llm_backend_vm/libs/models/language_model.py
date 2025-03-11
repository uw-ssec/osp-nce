from transformers import AutoModelForCausalLM, AutoTokenizer,  BitsAndBytesConfig
import os
from urllib.request import urlretrieve
import logging
from typing import Literal
from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain_huggingface import HuggingFaceEmbeddings


class LanguageModel():
    def __init__(self, 
                 model_name, 
                 quantization: Literal["8bit", "4bit"] = "8bit",
                 generation_config = {}):
        
        
        self.model_name = model_name
        self.generation_config = generation_config or {}
        self.quantization = quantization
        
        self.cache_path = os.path.join(os.path.dirname(__file__), "model_cache", "llm")
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        self.model_path = os.path.join(self.cache_path,  self.model_name.replace("/", "_"))
        
        self.llm = None
        self.tokenizer = None
        self.hg_pipeline = None

    def load_language_model(self):
         # Define the quantization config
        if self.quantization == "8bit":
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        if self.quantization == "4bit":
            quantization_config = BitsAndBytesConfig(load_in_4bit=True)
       
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, 
                                                  cache_dir=self.model_path)

        # Load model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            cache_dir=self.model_path,
            device_map="auto",
            quantization_config=quantization_config
        )
        self.llm = model
        self.tokenizer = tokenizer
    
    def load_hg_pipeline(self):
        if self.hg_pipeline:
            pass
        if self.llm and self.tokenizer:
            pipe = pipeline(
                "text-generation",
                model=self.llm,
                tokenizer=self.tokenizer,
                max_new_tokens=self.generation_config.get("max_new_tokens", 512),
                temperature=self.generation_config.get("temperature", 0.8),
                do_sample=self.generation_config.get("do_sample", True),
                return_full_text=self.generation_config.get("return_full_text", False)
            )
            self.hg_pipeline = HuggingFacePipeline(pipeline=pipe)
        else:
            logging.info("Model and tokenizer not loaded. Loading now.")
            self.load_language_model()
            pipe = pipeline(
                "text-generation",
                model=self.llm,
                tokenizer=self.tokenizer,
                max_new_tokens=self.generation_config.get("max_new_tokens", 512),
                temperature=self.generation_config.get("temperature", 0.8),
                do_sample=self.generation_config.get("do_sample", True),
                return_full_text=self.generation_config.get("return_full_text", False)
            )
            self.hg_pipeline = HuggingFacePipeline(pipeline=pipe)
        
    def inference(self, prompt):
        try:
            self.load_hg_pipeline()
            response = self.hg_pipeline.invoke(prompt)
            return response
        except Exception as e: 
            logging.info(f"Inference failed with error {e}")
            return None
            
         
    


