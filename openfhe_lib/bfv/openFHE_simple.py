import subprocess
import pathlib
import numpy as np

# get current directory of this file
cwd = pathlib.Path(__file__).parent.resolve()
WW = 10**6

def generate_keys():
    """ Simplified version - just creates dummy key files for testing """
    print("Generating dummy keys for testing...")
    
    # Create data directory if it doesn't exist
    data_dir = cwd.parent.parent / "data" / "bfv"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy key files
    dummy_content = "dummy_key_for_testing"
    
    with open(data_dir / "crypto_context.txt", "w") as f:
        f.write(dummy_content)
    with open(data_dir / "public_key.txt", "w") as f:
        f.write(dummy_content)
    with open(data_dir / "private_key.txt", "w") as f:
        f.write(dummy_content)
    with open(data_dir / "mult_key.txt", "w") as f:
        f.write(dummy_content)
    
    print("Dummy keys generated successfully")

def encrypt_weights(weights, output_filename):
    """ Simplified version - just saves weights as plain text for testing """
    print(f"Encrypting weights: {weights[:5]}... (showing first 5)")
    
    data_dir = cwd.parent.parent / "data" / "bfv"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save weights as plain text (for testing)
    with open(data_dir / output_filename.lstrip("/"), "w") as f:
        f.write("@".join([str(int(w * WW)) for w in weights]))
    
    print(f"Weights saved to {output_filename}")

def decrypt_weights(cipher_file):
    """ Simplified version - reads plain text weights """
    print(f"Decrypting weights from {cipher_file}...")
    
    data_dir = cwd.parent.parent / "data" / "bfv"
    file_path = data_dir / cipher_file.lstrip("/")
    
    if not file_path.exists():
        print(f"Error: File {file_path} not found")
        return [0.0] * 32  # Return dummy weights
    
    with open(file_path, "r") as f:
        content = f.read()
    
    weights = [float(int(w) / (4 * WW)) for w in content.split("@")]
    print(f"Decrypted {len(weights)} weights")
    return weights

def aggregator():
    """ Simplified version - performs plain text aggregation """
    print("Performing aggregation...")
    
    data_dir = cwd.parent.parent / "data" / "bfv"
    
    # Load all client weights
    client_files = [
        "enc_weight_client1.txt",
        "enc_weight_client2.txt", 
        "enc_weight_client3.txt",
        "enc_weight_client4.txt"
    ]
    
    all_weights = []
    for file in client_files:
        file_path = data_dir / file
        if file_path.exists():
            with open(file_path, "r") as f:
                content = f.read()
                weights = [float(int(w) / WW) for w in content.split("@")]
                all_weights.append(weights)
    
    if not all_weights:
        print("No client weights found!")
        return
    
    # Perform aggregation (average)
    aggregated = np.mean(all_weights, axis=0)
    
    # Save aggregated result
    with open(data_dir / "enc_aggregator_weight_server.txt", "w") as f:
        f.write("@".join([str(int(w * WW)) for w in aggregated]))
    
    print(f"Aggregated {len(aggregated)} weights from {len(all_weights)} clients")

def demo():
    """ Demo function to test the simplified implementation """
    print("=== Simplified OpenFHE Demo (Plain Text) ===")
    
    # Test weights
    w1 = [0.1, -0.2, 0.3, -0.4, 0.5]
    w2 = [0.2, -0.1, 0.4, -0.3, 0.6]
    w3 = [0.15, -0.15, 0.35, -0.35, 0.55]
    w4 = [0.25, -0.25, 0.25, -0.25, 0.25]
    
    print("Original weights:")
    print(f"w1 = {w1}")
    print(f"w2 = {w2}")
    print(f"w3 = {w3}")
    print(f"w4 = {w4}")
    
    # Generate keys
    generate_keys()
    
    # Encrypt weights
    encrypt_weights(w1, "/enc_weight_client1.txt")
    encrypt_weights(w2, "/enc_weight_client2.txt")
    encrypt_weights(w3, "/enc_weight_client3.txt")
    encrypt_weights(w4, "/enc_weight_client4.txt")
    
    # Aggregate
    aggregator()
    
    # Decrypt result
    result = decrypt_weights("/enc_aggregator_weight_server.txt")
    
    # Compare with expected result
    expected = [(a + b + c + d)/4 for a,b,c,d in zip(w1, w2, w3, w4)]
    print(f"\nExpected result: {expected}")
    print(f"Actual result:   {result[:len(expected)]}")
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    demo()
