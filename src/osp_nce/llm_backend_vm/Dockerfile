# Use NVIDIA's official CUDA runtime image (CUDA 12.4 + cuDNN)
FROM nvidia/cuda:12.6.3-devel-ubuntu24.04 AS base
WORKDIR /app

# Install basic apt packages
RUN echo "Installing Apt-get packages..." \
    && apt-get update --fix-missing > /dev/null \
    && apt-get install -y wget zip tzdata curl git ca-certificates gnupg lsb-release > /dev/null \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install gcloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update \
    && apt-get install -y google-cloud-sdk

# Install Pixi manually 
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:${PATH}"

# Add runtime as NVIDIA for GPU access
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

COPY pixi.toml pixi.lock ./

RUN pixi install \
    && pixi shell-hook --shell bash > /etc/profile.d/pixi.sh

FROM base as backend
COPY ./serve /app/serve
COPY ./libs /app/libs
COPY ./tests /app/tests
EXPOSE 5000
EXPOSE 8501

CMD ["pixi", "run", "python", "serve/wsgi.py"]
