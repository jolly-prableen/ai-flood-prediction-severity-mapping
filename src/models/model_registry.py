from .cnn_lstm.model import CNNLSTM
from .cnn_transformer.model import CNNTransformer
from .resnet_bilstm.model import ResNetBiLSTM
from .unet_convlstm.model import UNetConvLSTM
from .attention_unet_lstm.model import AttentionUNetLSTM

MODEL_REGISTRY = {
    "CNN + LSTM": CNNLSTM,
    "CNN + Transformer": CNNTransformer,
    "ResNet + BiLSTM": ResNetBiLSTM,
    "U-Net + ConvLSTM": UNetConvLSTM,
    "Attention U-Net + LSTM": AttentionUNetLSTM,
}
