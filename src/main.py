import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import ToTensor

device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)
batch_size = 128
learning_rate = 1e-3
epochs = 20

class BasicImageClassify(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 16), 
            nn.ReLU(),
            nn.Linear(16, 16), 
            nn.ReLU(),
            nn.Linear(16, 16), 
            nn.ReLU(),
            nn.Linear(16, 10),
        )
        
    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits
    
class CNNClassify(nn.Module):
    def __init__(self, convs = [[20, 5, 1], [60, 5, 1]], linear = [512, 10], batch_norm = True):
        super().__init__()
        self.flatten = nn.Flatten()

        channels = 1
        out_size = 28

        self.conv_stack = nn.Sequential()
        for conv in convs:
            self.conv_stack.append(nn.Conv2d(channels, conv[0], conv[1], conv[2]))
            self.conv_stack.append(nn.ReLU())
            if batch_norm:
                self.conv_stack.append(nn.BatchNorm2d(conv[0]))
            self.conv_stack.append(nn.MaxPool2d(2, 2))
            out_size = ((out_size - conv[1]) / conv[2]) + 1
            out_size = ((out_size - 2) / 2) + 1
            channels = conv[0]

        out_size *= out_size * channels
        out_size = int(out_size)
        self.out_size = out_size

        self.linear_stack = nn.Sequential()
        for i in linear:
            self.linear_stack.append(nn.Linear(out_size, i))
            self.linear_stack.append(nn.ReLU())
            if batch_norm:
                self.linear_stack.append(nn.BatchNorm1d(i))
            out_size = i
    
    def forward(self, x):
        x = self.conv_stack(x)
        x = x.view(-1, self.out_size)
        logits = self.linear_stack(x)
        return logits
      
def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    for batch, (X, y) in enumerate(dataloader):
        # Compute prediction and loss
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")


def test_loop(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0

    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")  

def main():
    global device
    global batch_size
    global learning_rate
    global epochs
    
    training_data = datasets.MNIST(root="data", train=True, download=True, transform=ToTensor())
    test_data = datasets.MNIST(root="data", train=False, download=True, transform=ToTensor())

    # Create data loaders.
    train_dataloader = DataLoader(training_data, batch_size=batch_size)
    test_dataloader = DataLoader(test_data, batch_size=batch_size)
    
    model = CNNClassify([[20, 5, 1], [40, 3, 1]], [512, 1024, 10]).to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
    print("Using device:", device, "")

    for t in range(epochs):
        print(f"Epoch {t+1}\n-------------------------------")
        train_loop(train_dataloader, model, loss_fn, optimizer)
        test_loop(test_dataloader, model, loss_fn)

    torch.save(model.state_dict(), "models/basic_nn.pth")
    
main()
